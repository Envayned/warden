"""An AWS Python Pulumi program"""

import json

from pulumi import Config, Output, ResourceOptions, export
import pulumi_aws as aws
from iam import * # yikes, fix later

def setup_sso_infrastructure():
    # initialize pulumi config 
    config = Config("warden")
    users_config = config.require_object('users')

    # dictionaries for resources

    users = {}
    groups = {}
    account_assignments = {}

    # create users and groups based on config

    for user_name, user_data in users_config.items():
        user_name = user_data['name']
        user = create_identity_store_user(user_name)
        users[user_name] = user

        if 'group' in user_data:
            group_name = user_data['group']
            if group_name not in groups:
                group = create_identity_store_group(group_name, group_name, f"A group for {group_name} users")
                groups[group_name] = group

            create_identity_store_group_membership(groups[group_name], user)

    # create account assignments for users

    for user_key, user_data in users_config.items():
        user_name = user_data['name']
        user = users[user_name]
        policies = user_data["policies"]
        description = user_data["description"]

        permission_set_name = f"{user_name}_perm_set"
        permission_set = create_permission_set(permission_set_name, "PT1H", description=description)

        account_assignment_name = f"{user_name}_account_assignment"
        account_assignment = create_account_assignment(account_assignment_name, permission_set.arn, user)

        account_assignments[user_name] = account_assignment

        for policy_arn in policies:
            policy_attachment_name = f"{user_name}_PolicyAttachment_{policy_arn.split('/')[-1]}"
            create_policy_attachment(policy_attachment_name, permission_set.arn, policy_arn, account_assignment)

    # Export group names uggggghghhghghghghg
    # group_names = {group_name: group.id for group_name, group in groups.items()}
    # export("groupNames", Output.all(group_names))

    # # Export user information
    # user_names = {user_name: user.id for user_name, user in users.items()}
    # export("userNames", Output.all(user_names))


if __name__ == "__main__":
    setup_sso_infrastructure()

        





## because im only one person, i only have 1 user that i can log into, because i dont want to create a bunch of fake emails.
# my_user = aws.identitystore.get_user(identity_store_id=sso.identity_store_ids[0], 
#     alternate_identifier=aws.identitystore.GetUserAlternateIdentifierArgs(
#         unique_attribute=aws.identitystore.GetUserAlternateIdentifierUniqueAttributeArgs(
#             attribute_path="UserName",
#             attribute_value="hadi_dev",
#         ),
#     ))


# # create a new identity store group
# dev_group = aws.identitystore.Group(
#     "dev_users_store",
#     display_name="Devs Group",
#     identity_store_id=sso.identity_store_ids[0],
#     description="A group for dev users"
#     )

# runner_user = aws.identitystore.User(
#     "runner_user",
#     name={
#         "givenName": "Runner",
#         "familyName": "User",
#     },
#     identity_store_id=sso.identity_store_ids[0], # ouch
#     user_name="runner_user",
#     display_name="Runner User",
# )

# runner_group = aws.identitystore.Group(
#     "runner_users_store",
#     display_name="Runner Group",
#     identity_store_id=sso.identity_store_ids[0],
#     description="A group for runner users"
#     )

#  # Group memberships for the users
# dev_group_membership = aws.identitystore.GroupMembership("dev_group_membership",
#     group_id=dev_group.group_id,
#     identity_store_id=sso.identity_store_ids[0],
#     member_id=my_user.user_id,
# )


# dev_user = aws.identitystore.User(
#     "dev_user",
#     name={
#         "givenName": "Dev",
#         "familyName": "User1",
#     },
#     identity_store_id=sso.identity_store_ids[0],
#     user_name="dev_user",
#     display_name="lmaooo",
# )

# # create a permission set
# dev_permission_set = aws.ssoadmin.PermissionSet(
#     "dev_permission_set",
#     name="AdministratorAccess",
#     instance_arn=sso.arns[0],
#     session_duration="PT8H",
#     description="A permission set for devs users"
#     )

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

# # create an account assignment
# account_assignment = aws.ssoadmin.AccountAssignment("account_assignment",
#     instance_arn=sso.arns[0],
#     permission_set_arn=dev_permission_set.arn,
#     principal_id=dev_group.group_id,
#     principal_type="GROUP",
#     target_id=get_aws_account_id(),
#     target_type="AWS_ACCOUNT")

# # attach the policy to the account assignmnent 

# admin_managed_policy_attachment = aws.ssoadmin.ManagedPolicyAttachment("admin_managed_policy_attachment",
#     instance_arn=sso.arns[0],
#     permission_set_arn=dev_permission_set.arn,
#     managed_policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",
#     opts=ResourceOptions(depends_on=[account_assignment]))




# export('identity_store_group_id', dev_group.id)
# export("user", dev_user.name)
# export('runner_user', runner_user.name)
# # export("identity_store_id", sso.identity_store_ids[0])
# # export('runner_roleArn', runner_role.arn)
# export('dev_group_id', dev_group.group_id)
# export('runner_group_id', runner_group.group_id)
# export('myUser', my_user.user_name)