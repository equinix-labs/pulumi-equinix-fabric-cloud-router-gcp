import pulumi
import time
from google.cloud import compute_v1
from typing import Tuple, Optional

class CloudRouterPeerConfig(pulumi.ComponentResource):
    """
    A Pulumi component resource to manage Cloud Router peer configurations in Google Cloud.
    """
    def __init__(self, name: str, router_name: str, region: str, project_id: str, new_asn: int, opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__('extendedGcp:compute:CloudRouterPeerConfig', name, None, opts)
        
        self.compute_client = compute_v1.RoutersClient()

        self.router_name = router_name
        self.region = region
        self.project_id = project_id
        self.equinix_asn = new_asn

        pulumi.Output.all(router_name, region, project_id, new_asn).apply(
            lambda args: self.__update_bgp_peer(*args)
        )

        router_info = pulumi.Output.all(router_name, region, project_id).apply(
            lambda args: self.__fetch_router_info(*args)
        )

        self.gcp_asn = router_info.apply(lambda info: info.get('asn'))
        self.gcp_router_ip = router_info.apply(lambda info: info.get('gcp_router_ip'))
        self.equinix_router_ip = router_info.apply(lambda info: info.get('equinix_router_ip'))

        self.register_outputs({
            'router_name': router_name,
            'region': region,
            'project_id': project_id,
            'gcp_asn': self.gcp_asn,
            'equinix_asn': new_asn,
            'gcp_router_ip': self.gcp_router_ip,
            'equinix_router_ip': self.equinix_router_ip
        })

    def __update_bgp_peer(self, router_name: str, region: str, project_id: str, new_asn: int):
        router = self.__get_router(router_name, region, project_id)

        if not router.bgp_peers or len(router.bgp_peers) == 0:
            raise ValueError(f"No BGP peers found in router '{router_name}'")
        
        router.bgp_peers[0].peer_asn = new_asn

        update_request = compute_v1.PatchRouterRequest(
            project=project_id,
            region=region,
            router=router_name,
            router_resource=router
        )

        return self.compute_client.patch(request=update_request)

    def __fetch_router_info(self, router_name: str, region: str, project_id: str) -> dict:
        retries = 20
        for attempt in range(retries):
            try:
                router = self.__get_router(router_name, region, project_id)

                if not router.interfaces or not router.bgp_peers:
                    raise ValueError(f"Router '{router_name}' missing required interfaces or BGP peers")

                gcp_router_ip_cidr = router.interfaces[0].ip_range
                equinix_router_ip = router.bgp_peers[0].peer_ip_address

                if not gcp_router_ip_cidr or not equinix_router_ip:
                    raise ValueError("Empty IP range or peer IP address")

                gcp_router_ip, _ = self.__parse_cidr(gcp_router_ip_cidr)
                equinix_router_ip_with_mask = self.__append_subnet_mask(equinix_router_ip, _)

                return {
                    'asn': router.bgp.asn,
                    'gcp_router_ip': gcp_router_ip,
                    'equinix_router_ip': equinix_router_ip_with_mask
                }

            except ValueError as ve:
                if attempt == retries - 1:
                    raise ve
                else:
                    pulumi.log.warn(f"Attempt {attempt + 1}/{retries} failed: {str(ve)}")
                    time.sleep(10)

        # If all retries failed, raise an error
        raise RuntimeError(f"Failed to fetch router info after {retries} attempts")

    def __get_router(self, router_name: str, region: str, project_id: str) -> compute_v1.Router:
        """
        Fetches a router using the Google Cloud SDK.
        Args:
            router_name (str): The name of the router.
            region (str): The region where the router is located.
            project_id (str): The project ID.

        Returns:
            compute_v1.Router: The fetched router.
        """
        try:
            return self.compute_client.get(project=project_id, region=region, router=router_name)
        except Exception as e:
            raise ValueError(f"Error fetching router '{router_name}' in project '{project_id}': {str(e)}")

    def __parse_cidr(self, cidr: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extracts IP address and subnet mask from CIDR notation.

        Args:
            cidr (str): The CIDR notation string.

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the IP address and the subnet mask.
        """
        if cidr:
            ip, mask = cidr.split('/')
            return ip, mask
        return None, None

    def __append_subnet_mask(self, ip: str, mask: str) -> Optional[str]:
        """
        Appends subnet mask to an IP address.

        Args:
            ip (str): The IP address.
            mask (str): The subnet mask.

        Returns:
            Optional[str]: The IP address with subnet mask, if both are provided.
        """
        if ip and mask:
            return f"{ip}/{mask}"
        return None
