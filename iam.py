import pulumi_aws as aws

from pulumi import Config, Output

config = Config()
users_config = config.require_object('users')

## getters rq

def get_sso_instance_arn():
    return aws.ssoadmin.get_instances().arns[0]

def get_sso_identity_store_id():
    return aws.ssoadmin.get_instances().identity_store_ids[0]

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


def create_iam_user(user_name, policies):
    """
    Create an IAM user with the given name and attach the given policies to it.
    """
    user = aws.iam.User(user_name, force_destroy=True, name=user_name)
    for policy_arn in policies:
        aws.iam.UserPolicyAttachment(f"{user_name}-policy-attach",
            policy_arn=policy_arn,
            user=user.name)
    return user

def create_iam_role(role_name, description, user_arn):
    """
    Create an IAM role with the given name and description, which can be assumed by the given user.
    """
    return aws.iam.Role(role_name,
        description=description,
        assume_role_policy=assume_role_policy_for_principal({'AWS': user_arn}))

def create_identity_store_user(user_name):
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



def create_identity_store_group(group_name):
    """
    Create an identity store group with the given name.
    """
    return aws.identitystore.Group(group_name,
        identity_store_id=get_sso_identity_store_id,
        group_name=group_name,
        display_name=group_name)





