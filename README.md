# Pulumi Template to Connect Equinix Cloud Router with Google Cloud Platform via Equinix Fabric

<!-- TODO abstract -->

![](https://img.shields.io/badge/Stability-Experimental-red.svg)

This repository is [Experimental](https://github.com/packethost/standards/blob/master/experimental-statement.md) meaning that it's based on untested ideas or techniques and not yet established or finalized or involves a radically new and innovative style! This means that support is best effort (at best!) and we strongly encourage you to NOT use this in production.

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

<!-- TODO
## Configuration Variables

The following table lists the configuration variables for both templates:

| Variable | Description | Default Value |
|----------|-------------|---------------|

-->

To add them you can use `pulumi config set` command:

```sh
pulumi config set projectId <EQUINIX_FABRIC_PROJECT_ID>
```

## Customization

Feel free to customize the templates according to your specific requirements.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvement, please open an issue or submit a pull request.

## License

This project is licensed under the [Apache 2.0](LICENSE).
