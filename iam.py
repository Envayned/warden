import pulumi_aws as aws
import os

from dotenv import load_dotenv
from pulumi import Config, Output, ResourceOptions
from typing import Union
from pulumi_aws.identitystore import User, Group
from pulumi_aws.ssoadmin import AccountAssignment

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

def get_identity_store_user(user_name: str):
    """
    Return the user within the identity store with the given name.
    """
    return aws.identitystore.get_user(
        identity_store_id=get_sso_identity_store_id(),
        alternate_identifier=aws.identitystore.GetUserAlternateIdentifierArgs(
            unique_attribute=aws.identitystore.GetUserAlternateIdentifierUniqueAttributeArgs(
                attribute_path="UserName",
                attribute_value=user_name,
            ),
        )
    )

def get_identity_store_group(group_name: str): #uggghghghghghghghghh
    """
    Return the group within the identity store with the given name.
    """
    return aws.identitystore.get_group(
        identity_store_id=get_sso_identity_store_id(),
        alternate_identifier=aws.identitystore.GetGroupAlternateIdentifierArgs(
            unique_attribute=aws.identitystore.GetGroupAlternateIdentifierUniqueAttributeArgs(
                attribute_path="DisplayName",
                attribute_value=group_name,
            ),
        )
    )

def add_user_to_group(user_name: str, group_name: str): #TODO: i just want to add my user to the admin group, but brain mush
    return create_identity_store_group_membership(group_name, get_identity_store_user(user_name))

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

def create_identity_store_user(user_name: str):
    """
    Create an identity store user with the given name.
    """
    return aws.identitystore.User(user_name,
        identity_store_id=get_sso_identity_store_id(),
        user_name=user_name,
        name={
            "givenName": "John",
            "familyName": "Doe",
        }, 
        display_name=user_name)



def create_identity_store_group(group_name: str, display_name: str, description: str | None = None):
    """
    Create an identity store group with the given name.
    """
    return aws.identitystore.Group(group_name,
        identity_store_id=get_sso_identity_store_id(),
        display_name=display_name, 
        description=description)

def create_identity_store_group_membership(group: Group, user: User):
    """
    Add the given user to the given group.
    """
    return group.display_name.apply(lambda display_name: aws.identitystore.GroupMembership(f"{display_name}_membership",
        group_id=group.group_id,
        identity_store_id=get_sso_identity_store_id(),
        member_id=user.user_id))

def create_permission_set(permission_set_name: str, 
                          session_duration: str = "PT1H" , 
                          relay_state: str | None = None,
                          description: str | None = None):
    """
    Create a permission set with the given name, session duration, and relay state.
    """
    return aws.ssoadmin.PermissionSet(permission_set_name,
        instance_arn=get_sso_instance_arn(),
        session_duration=session_duration,
        relay_state=relay_state,
        description=description
        )



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

def create_policy_attachment(name: str, permission_set_arn: str, managed_policy_arn: str, account_assignment: AccountAssignment):
    """
    Create a policy attachment with the given name, permission set, and policy_arn.
    """
    return aws.ssoadmin.ManagedPolicyAttachment(name,
        instance_arn=get_sso_instance_arn(),
        permission_set_arn=permission_set_arn,
        managed_policy_arn=managed_policy_arn,
        opts=ResourceOptions(depends_on=[account_assignment])
    )



