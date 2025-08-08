from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Advertisement, AdvertisementCategory, AdvertisementImage


class AdvertisementCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvertisementCategory
        fields = ["id", "name", "image"]


class AdvertisementImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvertisementImage
        exclude = ["advertisement"]


class AdvertisementSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    images = AdvertisementImageSerializer(many=True, read_only=True)
    category = AdvertisementCategorySerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = ["id", "shop", "owner", "name", "description", "images", "category", "price", "phone", "status", "published", "address", "latitude", "longitude", "is_favorite", "created_at"]

    def get_is_favorite(self, obj):
        request = self.context.get("request")

        user = request.user if request and hasattr(request, "user") else None

        if user:
            return user in obj.favorited_by.all()

        return False


class CreateUpdateAdvertisementSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Advertisement
        exclude = ["owner", "published"]

    def to_representation(self, instance):
        return AdvertisementSerializer(instance, context=self.context).data

    def create(self, validated_data):
        images_ids = validated_data.pop("images")

        advertisement = super().create(validated_data)

        images = AdvertisementImage.objects.filter(pk__in=images_ids, advertisement__isnull=True)
        images.update(advertisement=advertisement)

        return advertisement

    def update(self, instance, validated_data):
        images_ids = validated_data.pop("images", None)

        advertisement = super().update(instance=instance, validated_data={**validated_data, "published": False})

        if images_ids is not None:
            current_image_ids = set(instance.images.values_list("id", flat=True))

            images_to_delete = current_image_ids - set(images_ids)
            images_to_add = set(images_ids) - current_image_ids

            instance.images.filter(id__in=images_to_delete).delete()

            images = AdvertisementImage.objects.filter(pk__in=images_to_add, advertisement__isnull=True)
            images.update(advertisement=instance)

        return advertisement
