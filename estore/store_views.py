from django.db import transaction as db_transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import StandardPagination
from users.models import User as UserProfile
from wallets.models import Transaction, Wallet

from .models import Order, Product


class StoreProductsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Product.objects.all().order_by("-created_at")
        category = request.query_params.get("category")
        search = request.query_params.get("search")

        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)

        data = [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "category": item.category,
                "price": str(item.price),
                "image_url": item.image_url,
                "created_at": item.created_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)


class StoreCheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        items = request.data.get("items", [])
        total_amount = request.data.get("total_amount")
        payment_type = request.data.get("payment_type", "wallet")

        if not items:
            return Response({"error": "items is required"}, status=status.HTTP_400_BAD_REQUEST)

        if total_amount is None:
            return Response({"error": "total_amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            total_amount = float(total_amount)
            if total_amount <= 0:
                return Response({"error": "total_amount must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({"error": "Invalid total_amount"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        with db_transaction.atomic():
            order_status = "pending"
            completed_at = None

            if payment_type == "wallet":
                try:
                    wallet = Wallet.objects.select_for_update().get(user_id=profile)
                except Wallet.DoesNotExist:
                    return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

                if float(wallet.espees) < total_amount:
                    return Response(
                        {"error": f"Insufficient balance. Available: {wallet.espees}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                wallet.espees -= total_amount
                wallet.save(update_fields=["espees", "updated_at"])

                Transaction.objects.create(
                    wallet_id=wallet,
                    transaction_type="purchase",
                    amount=total_amount,
                    currency="espees",
                    description="Store checkout",
                )

                order_status = "completed"
                completed_at = timezone.now()

            order = Order.objects.create(
                user_id=profile,
                items=items,
                total_amount=total_amount,
                payment_type=payment_type,
                status=order_status,
                completed_at=completed_at,
            )

        return Response(
            {
                "id": str(order.id),
                "user_id": str(order.user_id_id),
                "items": order.items,
                "total_amount": str(order.total_amount),
                "payment_type": order.payment_type,
                "status": order.status,
                "created_at": order.created_at,
                "completed_at": order.completed_at,
            },
            status=status.HTTP_201_CREATED,
        )


class StoreOrdersMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        queryset = Order.objects.filter(user_id=profile).order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)

        data = [
            {
                "id": str(item.id),
                "items": item.items,
                "total_amount": str(item.total_amount),
                "payment_type": item.payment_type,
                "status": item.status,
                "created_at": item.created_at,
                "completed_at": item.completed_at,
            }
            for item in page
        ]
        return paginator.get_paginated_response(data)
