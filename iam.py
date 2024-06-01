import pulumi_aws as aws
import os

from dotenv import load_dotenv
from pulumi import Config, Output
from typing import Union
from pulumi_aws.identitystore import User, Group

config = Config()
users_config = config.require_object('users')
load_dotenv()

## getters rq

def get_sso_instance_arn():
    return aws.ssoadmin.get_instances().arns[0]

def get_sso_identity_store_id():
    return aws.ssoadmin.get_instances().identity_store_ids[0]

def get_aws_account_id():
    return os.getenv('AWS_ACCOUNT_ID')

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


# def create_iam_user(user_name, policies):
#     """
#     Create an IAM user with the given name and attach the given policies to it.
#     """
#     user = aws.iam.User(user_name, force_destroy=True, name=user_name)
#     for policy_arn in policies:
#         aws.iam.UserPolicyAttachment(f"{user_name}-policy-attach",
#             policy_arn=policy_arn,
#             user=user.name)
#     return user

# def create_iam_role(role_name: str, description: str, user_arn: str):
#     """
#     Create an IAM role with the given name and description, which can be assumed by the given user.
#     """
#     return aws.iam.Role(role_name,
#         description=description,
#         assume_role_policy=assume_role_policy_for_principal({'AWS': user_arn}))

def create_identity_store_user(user_name: str):
    """
    Create an identity store user with the given name.
    """
    return aws.identitystore.User(user_name,
        identity_store_id=get_sso_identity_store_id,
        user_name=user_name,
        name={
            "givenName": "John",
            "familyName": "Doe",
        }, 
        display_name=user_name)



def create_identity_store_group(group_name: str):
    """
    Create an identity store group with the given name.
    """
    return aws.identitystore.Group(group_name,
        identity_store_id=get_sso_identity_store_id,
        group_name=group_name,
        display_name=group_name)

def create_identity_store_group_membership(group: str, user: str):
    """
    Add the given user to the given group.
    """
    return aws.identitystore.GroupMembership(f"{group}-membership",
        group_id=group.id,
        identity_store_id=get_sso_identity_store_id,
        member_id=user.id)

def create_permission_set(permission_set_name: str, 
                          session_duration: str = "PT1H" , 
                          relay_state: str | None = None):
    """
    Create a permission set with the given name, session duration, and relay state.
    """
    return aws.ssoadmin.PermissionSet(permission_set_name,
        instance_arn=get_sso_instance_arn(),
        session_duration=session_duration,
        relay_state=relay_state)


def create_account_assignment(name: str, permission_set_arn: str, principal: Union[User, Group]):
    """
    Create an account assignment with the given name, permission set, and principal.
    """

    if isinstance(principal, User):
        principal = principal.user_id
        principal_type = "USER"
    elif isinstance(principal, Group):
        principal = principal.group_id
        principal_type = "GROUP"
    else:
        raise ValueError("Principal must be a User or Group")

    return aws.ssoadmin.AccountAssignment(name,
        instance_arn=get_sso_instance_arn(),
        permission_set_arn=permission_set_arn,
        principal_type=principal_type,
        principal_id=principal,
        target_id=get_aws_account_id(),
        target_type="AWS_ACCOUNT"
    )




