"""An AWS Python Pulumi program"""

import json

from pulumi import Config, Output, ResourceOptions, export
import pulumi_aws as aws

# declare a const for the account id 
AWS_ACCOUNT_ID = "252705693666"

def assume_role_policy_for_principal(principal):
    """
    Returns a well-formed policy document which can be used to control which principals may assume an IAM Role,
    by granting the `sts:AssumeRole` action to the given principal.
    """
    return Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
            "Sid": "AllowAssumeRole",
            "Effect": "Allow",
            "Principal": principal,
            "Action": "sts:AssumeRole",
            }
        ]
    })

config = Config()

## create an iam user and role for github runners
runner_iam_user = aws.iam.User(
    'runner_user',
    force_destroy=True,
    name='runner_user',
    )

runner_role = aws.iam.Role(
    'runner_role',
    description='role w/ deployment permissions',
    assume_role_policy=assume_role_policy_for_principal({'AWS': runner_iam_user.arn})
    )

dev_iam_user = aws.iam.User("dev_user",
    force_destroy=True,
    name="dev_user",
    )

dev_role = aws.iam.Role(
    'dev_role',
    description='role w/ service access',
    assume_role_policy=assume_role_policy_for_principal({'AWS': dev_iam_user.arn})
    )

sso = aws.ssoadmin.get_instances()
example_get_user = aws.identitystore.get_user(identity_store_id=sso.identity_store_ids[0], 
    alternate_identifier=aws.identitystore.GetUserAlternateIdentifierArgs(
        unique_attribute=aws.identitystore.GetUserAlternateIdentifierUniqueAttributeArgs(
            attribute_path="UserName",
            attribute_value="hadi_dev",
        ),
    ))


# create a new identity store group
dev_group = aws.identitystore.Group(
    "dev_users_store",
    display_name="Devs Group",
    identity_store_id=sso.identity_store_ids[0],
    description="A group for dev users"
    )

runner_user = aws.identitystore.User(
    "runner_user",
    name={
        "givenName": "Test",
        "familyName": "User2",
    },
    identity_store_id=sso.identity_store_ids[0], # ouch
    user_name="runner_user",
    display_name="lmaooo",
)

runner_group = aws.identitystore.Group(
    "runner_users_store",
    display_name="Runner Group",
    identity_store_id=sso.identity_store_ids[0],
    description="A group for runner users"
    )

 # Group memberships for the users
dev_group_membership = aws.identitystore.GroupMembership("dev_group_membership",
    group_id=dev_group.group_id,
    identity_store_id=sso.identity_store_ids[0],
    member_id=example_get_user.user_id,
)


dev_user = aws.identitystore.User(
    "dev_user",
    name={
        "givenName": "Dev",
        "familyName": "User1",
    },
    identity_store_id=sso.identity_store_ids[0],
    user_name="dev_user",
    display_name="lmaooo",
)

# create a permission set
dev_permission_set = aws.ssoadmin.PermissionSet(
    "dev_permission_set",
    name="devs-example-set",
    instance_arn=sso.arns[0],
    session_duration="PT8H",
    description="A permission set for devs users"
    )

# attach the permission set to the dev group

# dev_permission_set_attachment = aws.ssoadmin.PermissionSetInlinePolicy(
#     "dev_permission_set_attachment",
#     instance_arn=sso.arns[0],
#     permission_set_arn=dev_permission_set.arn,
#     inline_policy=Output.all(dev_group.group_id, dev_role.arn).apply(
#         lambda args: json.dumps({
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Action": "sts:AssumeRole",
#                     "Resource": args[1]
#                 }
#             ]
#         })
# ))

# create an account assignment
account_assignment = aws.ssoadmin.AccountAssignment("account_assignment",
    instance_arn=sso.arns[0],
    permission_set_arn=dev_permission_set.arn,
    principal_id=dev_group.group_id,
    principal_type="GROUP",
    target_id=AWS_ACCOUNT_ID,
    target_type="AWS_ACCOUNT")

# attach the policy to the account assignmnent 

admin_managed_policy_attachment = aws.ssoadmin.ManagedPolicyAttachment("admin_managed_policy_attachment",
    instance_arn=sso.arns[0],
    permission_set_arn=dev_permission_set.arn,
    managed_policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",
    opts=ResourceOptions(depends_on=[account_assignment]))




export('identity_store_group_id', dev_group.id)
export("user", dev_user.name)
export('runner_user', runner_user.name)
# export("identity_store_id", sso.identity_store_ids[0])
# export('runner_roleArn', runner_role.arn)
export('dev_group_id', dev_group.group_id)
export('runner_group_id', runner_group.group_id)
export('myUser', example_get_user.user_name)