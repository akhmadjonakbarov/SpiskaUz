from common.permissions import BaseEditDeleteObjectPermission


class CanEditDeleteAdvertisement(BaseEditDeleteObjectPermission):
    model_name = "advertisement"
