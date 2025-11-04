from django.db.models import Avg
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.templatetags.rest_framework import data

from reviews.models import Review, Keyword, ReviewKeyword, ReviewImage
from reviews.serializer import ReviewSerializer, ReviewKeywordSerializer, KeywordSerializer, ReviewImageSerializer


class ReviewViewSet(viewsets.ModelViewSet):
	queryset = Review.objects.all()
	serializer_class = ReviewSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=data)
		serializer.is_valid(raise_exception=True)
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		queryset = Review.objects.all()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	@action(detail=False, methods=["get"])
	def rating_average(self, request, *args, **kwargs):
		product_id = request.query_params.get("product_id")
		if not product_id:
			return Response(
				{"detail": "product_id 쿼리 파라미터가 필요합니다."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		avg_rating = Review.objects.filter(product_id=product_id).aggregate(
			average=Avg("rating")
		)["average"]

		return Response(
			{"product_id": product_id, "average_rating": round(avg_rating or 0, 2)},
			status=status.HTTP_200_OK,
		)  #모름..


class ReviewKeywordViewSet(viewsets.ModelViewSet):
	queryset = Review.objects.all()
	serializer_class = ReviewKeywordSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()#reviews.py에 유저 필드가 없어서 비워둠
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		review_id = request.query_params.get("review_id")
		queryset = self.queryset
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
		serializer.save() #reviews.py에 유저 필드가 없어서 비워둠
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		keywords = Keyword.objects.all()
		serializer = self.get_serializer(keywords, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)



class ReviewImageViewSet(viewsets.ModelViewSet):
	queryset = ReviewImage.objects.all()
	serializer_class = ReviewImageSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()  #reviews.py에 유저 필드가 없어서 비워둠
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	def list(self, request, *args, **kwargs):
		queryset = ReviewImage.objects.all()
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
