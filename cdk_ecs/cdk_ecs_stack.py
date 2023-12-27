from aws_cdk import (
    core,
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs
)
from constructs import Construct


class CdkEcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = self.create_vpc()
        taskdef = self.create_ecs_taskdef()
        self.create_ecs(vpc, taskdef)

    def create_vpc(self) -> ec2.Vpc:
        vpc = ec2.Vpc(self, "dev-vpc-01", vpc_name="dev-vpc-01",
                      ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
                      max_azs=2,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(
                              name="dev-public-subnet",
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=24
                          ),
                          ec2.SubnetConfiguration(
                              name="dev-private-subnet",
                              subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                              cidr_mask=24
                          )])

        # TODO
        # create vpc endpoint for ecs service access ecr

        return vpc

    def create_ecs_taskdef(self) -> ecs.FargateTaskDefinition:
        task_role = iam.Role(self, "TaskRole",
                             assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        execution_role = iam.Role(self, "ExecutionRole",
                                  assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        execution_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "service-role/AmazonECSTaskExecutionRolePolicy"))

        account_id = core.Aws.account_id
        taskdef = ecs.FargateTaskDefinition(self,
                                            "dev-ecs-taskdef",
                                            task_role=task_role,
                                            execution_role=execution_role)
        taskdef.add_container("dev-ecs-container",
                              image=ecs.ContainerImage.from_registry(f"{account_id}.dkr.ecr.ap-northeast-1.amazonaws.com/ecs-test-service-a-flask-app:latest"))
        return taskdef

    def create_ecs(self, vpc, taskdef):
        cluster = ecs.Cluster(self, "dev-ecs-cluster", vpc=vpc)
        ecs_service = ecs.FargateService(
            self,
            "dev-ecs-serviec",
            cluster=cluster,
            task_definition=taskdef,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )
