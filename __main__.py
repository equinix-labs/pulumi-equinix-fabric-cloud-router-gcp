import os
import sys
import pulumi
import pulumi_equinix as equinix
import pulumi_google_native as gcp
sys.path.insert(0, os.getcwd())
from extended_gcp import CloudRouterPeerConfig


# Configuration
config = pulumi.Config()
account_num = config.require_int("accountNum")
project_id = config.require("projectId")
notification_emails = config.require_object("notificationEmails")
equinix_metro = config.get("metro") or "FR"
speed_in_mbps = config.get_int("speedInMbps") or 100
purchase_order_num = config.get("purchaseOrderNum") or "1234"
gcp_project = config.require("gcpProject")
gcp_region = config.get("gcpRegion") or "europe-west3"

# Google Cloud VPC Network
gcp_vpc_network = gcp.compute.v1.Network(
    "vpcNetwork",
    project=gcp_project,
    name="pulumi-demo-network",
    auto_create_subnetworks=True
)

# Google Cloud Router
gcp_cloud_router = gcp.compute.v1.Router(
    "cloudRouter",
    project=gcp_project,
    region=gcp_region,
    name="pulumi-demo-router",
    network=gcp_vpc_network.self_link,
    bgp=gcp.compute.v1.RouterBgpArgs(
        asn=16550  # 16550 - ASN required for Partner Interconnect
    )
)

# Google Cloud VLAN Attachment (Interconnect)
gcp_vlan_attachment = gcp.compute.v1.InterconnectAttachment(
    "vlanAttachment",
    project=gcp_project,
    region=gcp_region,
    name="pulumi-demo-vlan-attach",
    router=gcp_cloud_router.self_link,
    type="PARTNER",
    edge_availability_domain="AVAILABILITY_DOMAIN_1",
    opts=pulumi.ResourceOptions(depends_on=[gcp_cloud_router])
)

# Equinix Fabric CloudRouter
fabric_cloud_router = equinix.fabric.CloudRouter(
    "cloudRouter",
    name="pulumi-demo-fcr-gcp",
    type="XF_ROUTER",
    location=equinix.fabric.CloudRouterLocationArgs(metro_code=equinix_metro),
    package=equinix.fabric.CloudRouterPackageArgs(code="STANDARD"),
    notifications=[equinix.fabric.CloudRouterNotificationArgs(
        type="ALL", emails=notification_emails)],
    order=equinix.fabric.CloudRouterOrderArgs(
        purchase_order_number=purchase_order_num,
    ),
    account=equinix.fabric.CloudRouterAccountArgs(account_number=account_num),
    project=equinix.fabric.CloudRouterProjectArgs(project_id=project_id),
    opts=pulumi.ResourceOptions(
        depends_on=[gcp_vlan_attachment],
        ignore_changes=["location"]  # Ignore changes due to known Pulumi issue
    )
)

# Service Profile lookup - Google Cloud
service_profile_gcp = equinix.fabric.get_service_profiles(
    filter=equinix.fabric.GetServiceProfilesFilterArgs(
        property="/name",
        operator="=",
        values=["Google Cloud Partner Interconnect Zone 1"],
    ),
)

# Fabric Connection creation - Google Cloud
fabric_connection_gcp = equinix.fabric.Connection("connection",
    name="pulumi-demo-fcr-gcp",
    type="IP_VC",
    notifications=[equinix.fabric.ConnectionNotificationArgs(
        type="ALL", emails=notification_emails)],
    order=equinix.fabric.ConnectionOrderArgs(
        purchase_order_number=purchase_order_num,
    ),
    bandwidth=speed_in_mbps,
    redundancy=equinix.fabric.ConnectionRedundancyArgs(priority="PRIMARY"),
    a_side=equinix.fabric.ConnectionASideArgs(
        access_point=equinix.fabric.ConnectionASideAccessPointArgs(
            type="CLOUD_ROUTER",
            router=equinix.fabric.ConnectionASideAccessPointRouterArgs(
                uuid=fabric_cloud_router.id
            )
        )
    ),
    z_side=equinix.fabric.ConnectionZSideArgs(
        access_point=equinix.fabric.ConnectionZSideAccessPointArgs(
            type="SP",
            authentication_key=gcp_vlan_attachment.pairing_key,
            seller_region=gcp_region,
            profile=equinix.fabric.ConnectionZSideAccessPointProfileArgs(
                type=service_profile_gcp.data[0].type,
                uuid=service_profile_gcp.data[0].uuid,
            ),
            location=equinix.fabric.ConnectionZSideAccessPointLocationArgs(
                metro_code=equinix_metro,
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[fabric_cloud_router],
        ignore_changes=["redundancy", "order"]
    ),
)

# Configure bgp peer ASN (Equinix ASN) in Google Cloud Router
# Initialize CloudRouterPeerConfig only after the dependencies are ready
gcp_peer_config = fabric_connection_gcp.id.apply(
    lambda _: CloudRouterPeerConfig(
        'peerConfig',
        gcp_cloud_router.name,
        gcp_region,
        gcp_project,
        fabric_cloud_router.equinix_asn
    )
)

# Configure bgp in Equinix Fabric side
routing_protocol_direct_gcp = equinix.fabric.RoutingProtocol("RoutingProtocolDirect",
    name="FabricToGCPRoutingProtocolDirect",
    type="DIRECT",
    connection_uuid=fabric_connection_gcp.id,
    direct_ipv4=equinix.fabric.RoutingProtocolDirectIpv4Args(
        equinix_iface_ip= gcp_peer_config.equinix_router_ip
    )
)

routing_protocol_bgp_gcp = equinix.fabric.RoutingProtocol("RoutingProtocolBGP",
    opts=pulumi.ResourceOptions(
        depends_on=[routing_protocol_direct_gcp],
    ),
    type="BGP",
    connection_uuid=fabric_connection_gcp.id,
    name="FabricToGCPRoutingProtocolBGP",
    customer_asn=gcp_peer_config.gcp_asn,
    bgp_ipv4=equinix.fabric.RoutingProtocolBgpIpv4Args(
        customer_peer_ip=gcp_peer_config.gcp_router_ip
    ),
)

# Export relevant data
pulumi.export("equinix_fabric_routing_protocol_gcp_bgp_state", routing_protocol_bgp_gcp.state)
pulumi.export("equinix_fabric_connection_gcp_id", fabric_connection_gcp.id)
pulumi.export("equinix_fabric_cloud_router_id", fabric_cloud_router.id)
pulumi.export("equinix_fabric_cloud_router_gcp_ip", gcp_peer_config.equinix_router_ip)
pulumi.export("equinix_asn", gcp_peer_config.equinix_asn)
pulumi.export("gcp_cloud_router_ip", gcp_peer_config.gcp_router_ip)
pulumi.export("gcp_asn", gcp_peer_config.gcp_asn)
