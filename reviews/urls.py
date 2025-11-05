from rest_framework.routers import DefaultRouter

from reviews.views import KeywordViewSet, ReviewImageViewSet, ReviewViewSet

router = DefaultRouter()
router.register("keywords", KeywordViewSet)
router.register("reviews", ReviewViewSet)
router.register("reviews_image", ReviewImageViewSet)

urlpatterns = router.urls
