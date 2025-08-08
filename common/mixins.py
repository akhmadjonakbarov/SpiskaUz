class ActionPermissionMixin:
    action_permissions = {}

    def get_permissions(self):
        permissions = []

        for actions, perms in self.action_permissions.items():
            if isinstance(actions, str) and self.action == actions or isinstance(actions, tuple) and self.action in actions:
                permissions.extend(perms)
                break
        else:
            permissions.extend(self.permission_classes)

        return [permission() for permission in permissions]
