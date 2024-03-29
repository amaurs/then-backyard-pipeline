import os

import aws_cdk as cdk
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_lambda import Function, Runtime, Architecture, Code
from aws_cdk.aws_route53 import HostedZone, CfnRecordSet, ZoneDelegationRecord
from aws_cdk.aws_s3 import Bucket, CorsRule, HttpMethods, BlockPublicAccess
from aws_cdk.aws_iam import PolicyStatement, Policy
from aws_cdk.aws_apigateway import RestApi, LambdaIntegration, Cors, AuthorizationType, CorsOptions, MethodOptions

from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Deployment of chalice custom domain on cdk is based on https://github.com/aws/chalice/issues/1728

        aphex_domain = "then.gallery"
        domain_name = f"if.{aphex_domain}"

        hosted_zone = HostedZone(
            self,
            "ThenBackyardHostedZone",
            zone_name=domain_name,

        )

        # Using a zone delegation record was taken from https://bahr.dev/2020/09/01/multiple-frontends/

        ZoneDelegationRecord(
            self,
            "ThenBackyardZoneDelegationRecord",
            record_name=domain_name,
            name_servers=hosted_zone.hosted_zone_name_servers,
            zone=HostedZone.from_hosted_zone_attributes(
                self, "ThenHostedZone",
                hosted_zone_id=os.getenv("THEN_HOSTED_ZONE_ID"),
                zone_name=aphex_domain),
            ttl=cdk.Duration.minutes(1)  # TODO: should increase this value once everything works
        )

        acm_cert = Certificate(
            self,
            "ThenBackyardCertificate",
            domain_name=domain_name,
            validation=CertificateValidation.from_dns(hosted_zone)
        )

        bucket = Bucket(
            self,
            "ThenBackyardBucket",
            versioned=True,
            bucket_name=domain_name,
            block_public_access=BlockPublicAccess.BLOCK_ALL,
            cors=[
                CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[HttpMethods.PUT, HttpMethods.POST, HttpMethods.GET, HttpMethods.DELETE],
                    allowed_origins=["*"]
                )
            ])

        api_version = "v0"

        chalice = Chalice(
            self,
            'ChaliceApp',
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "EDGE",
                "api_gateway_custom_domain": {
                    "domain_name": domain_name,
                    "certificate_arn": acm_cert.certificate_arn,
                },
                "api_gateway_stage": api_version,
                "environment_variables": {
                    'S3_BUCKET_NAME': domain_name,
                    'JWT_SECRET_NAME': os.getenv("JWT_SECRET_NAME"),
                    'HASHED_PASSWORD_SECRET_NAME': os.getenv("HASHED_PASSWORD_SECRET_NAME")
                }
            }
        )

        getSecretPolicyStatement = PolicyStatement(
            actions=['secretsmanager:GetSecretValue'],
            resources=['arn:aws:secretsmanager:us-east-1:892700351551:secret:*'])

        chalice.get_role('DefaultRole').attach_inline_policy(
            policy=Policy(scope=self, id='GetSecretPolicy', statements=[getSecretPolicyStatement]))

        bucket.grant_read_write(
            chalice.get_role('DefaultRole')
        )

        custom_domain = chalice.get_resource("ApiGatewayCustomDomain")
        CfnRecordSet(
            self,
            "ThenBackyardAPISubdomain",
            hosted_zone_id=hosted_zone.hosted_zone_id,
            name=domain_name,
            type="A",
            alias_target=CfnRecordSet.AliasTargetProperty(
                dns_name=custom_domain.get_att("DistributionDomainName").to_string(),
                hosted_zone_id=custom_domain.get_att(
                    "DistributionHostedZoneId"
                ).to_string(),
                evaluate_target_health=False,
            ),
        )

        api = RestApi.from_rest_api_attributes(
            self,
            'RestAPI',
            rest_api_id=chalice.get_resource("RestAPI").get_att("RestApiId").to_string(),
            root_resource_id=chalice.get_resource("RestAPI").get_att("RootResourceId").to_string())

        flora = api.root.add_resource(
            "flora",
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_methods=Cors.ALL_METHODS,
                allow_headers=Cors.DEFAULT_HEADERS),
            default_method_options=MethodOptions(authorization_type=AuthorizationType.NONE))

        integration = LambdaIntegration(Function(
            self,
            "ThenBackendLambda",
            runtime=Runtime.PROVIDED_AL2,
            architecture=Architecture.ARM_64,
            handler="bootstrap",
            code=Code.from_asset(path="../rust-runtime/target/lambda/then-backend"),
            function_name="ThenBackend",
            environment={
                "TIMESTAMP": os.getenv("TIMESTAMP")
            },
        ))

        # The fractal resource was created to return png images. Api Gateway transforms the response
        # from the lambda. The request should include an Accept header that specifies the Content-Type.
        # If not present, Api Gateway will assume the default value which is application/json. On the
        # other hand, the response from the lambda should have the body encoded to base64 and contain
        # the field isBase64Encoded set as true. Additionally, the resource should be configured to
        # accept the appropriate binary media type, in this case image/png.
        fractal = api.root.add_resource(
            "fractal",
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_methods=Cors.ALL_METHODS,
                allow_headers=Cors.DEFAULT_HEADERS),
            default_method_options=MethodOptions(authorization_type=AuthorizationType.NONE))

        fractal.add_proxy(
            any_method=True,
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_methods=Cors.ALL_METHODS,
                allow_headers=Cors.DEFAULT_HEADERS),
            default_integration=integration,
            default_method_options=MethodOptions(authorization_type=AuthorizationType.NONE)
        )

        flora.add_method('GET', integration)
