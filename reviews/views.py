from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from reviews.models import Review, Keyword, ReviewKeyword, ReviewImage
from reviews.serializer import (
    ReviewSerializer,
    ReviewKeywordSerializer,
    KeywordSerializer,
    ReviewImageSerializer,
    RatingAverageSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
	queryset = Review.objects.all()
	serializer_class = ReviewSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		queryset = Review.objects.all()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	@action(detail=False, methods=["get"], url_path="rating-average", url_name="rating_average")
	def rating_average(self, request, *args, **kwargs):
		serializer = RatingAverageSerializer(data=request.query_params)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewKeywordViewSet(viewsets.ModelViewSet):
	queryset = ReviewKeyword.objects.all()
	serializer_class = ReviewKeywordSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		review_id = request.query_params.get("review_id")
		queryset = self.get_queryset()
		if review_id:
				queryset = queryset.filter(review_id=review_id)
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)



class KeywordViewSet(viewsets.ModelViewSet):
	queryset = Keyword.objects.all()
	serializer_class = KeywordSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		queryset = self.get_queryset()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)



class ReviewImageViewSet(viewsets.ModelViewSet):
	queryset = ReviewImage.objects.all()
	serializer_class = ReviewImageSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		queryset = self.get_queryset()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
