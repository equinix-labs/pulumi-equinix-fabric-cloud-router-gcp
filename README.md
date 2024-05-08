# Pulumi Template to Connect Equinix Fabric Cloud Router (FCR) with Google Cloud Platform via Equinix Fabric

This Pulumi template sets up an end-to-end Layer 2 connection using Google Cloud Interconnect through Equinix Fabric from a new Equinix Fabric Cloud Router (FCR) to a Google Cloud Router. As a peculiarity, this template uses the python library google-cloud-compute to cover some functionality not available (May 2024) in the Pulumi provider for GCP, necessary to complete the configuration and establish the BGP session.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [Python](https://www.python.org/downloads/)

## Getting Started

Create a new Pulumi project:

- `pulumi new https://github.com/equinix-labs/pulumi-equinix-fabric-cloud-router-gcp`


## Usage

1. Activate the virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Set the required configuration variables. See [configuration variables](#configuration-variables) below.
4. Set metal credentials: `export METAL_AUTH_TOKEN=<YOUR_METAL_API_TOKEN>`
5. Deploy the stack: `pulumi up`
6. Follow the instructions printed in the console to complete the deployment.

## Configuration Variables

The following table lists the configuration variables for both templates:

| Variable | Description | Type | Default | Required |
|----------|-------------|------|---------|----------|
| accountNum | Equinix Fabric billing account number | `integer` | n/a | yes |
| projectId | Equinix Fabric project Id | `string` | n/a | yes |
| notificationEmails | Array of contact emails | `list(string)` | n/a | yes |
| gcpProject | The default GCP project to manage resources in | `string` | n/a | yes |
| metro | Two-letter code indicating the metropolitan area for the new resources | `string` | "FR" | no |
| speedInMbps | Equinx Fabric connection bandwidth in Mbps | `integer` | 100 | no |
| purchaseOrderNum | Equinix Fabric Purchase order number | `string` | "1234" | no |
| gcpRegion | Region where the GCP resources resides | `string` | "europe-west3" | no |


To add them you can use `pulumi config set` command:

```sh
pulumi config set projectId <EQUINIX_FABRIC_PROJECT_ID>
$ pulumi config set accountNum 1234
$ pulumi config set projectId 5678
$ pulumi config set gcpProject myGCPProject
$ pulumi config set --path 'notificationEmails[0]' example@equinix.com
```

## Customization

Feel free to customize the templates according to your specific requirements.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the [Apache 2.0](LICENSE).
