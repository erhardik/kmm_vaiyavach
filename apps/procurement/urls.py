from django.urls import path

from apps.procurement.views import (
    GoodsReceiptCreateView,
    GoodsReceiptDeleteView,
    GoodsReceiptListView,
    GoodsReceiptUpdateView,
    PurchaseOrderCreateView,
    PurchaseOrderDeleteView,
    PurchaseOrderListView,
    PurchaseOrderLineCreateView,
    PurchaseOrderLineDeleteView,
    PurchaseOrderLineListView,
    PurchaseOrderLineUpdateView,
    PurchaseOrderUpdateView,
)

app_name = "procurement"

urlpatterns = [
    path("purchase-orders/", PurchaseOrderListView.as_view(), name="po-list"),
    path("purchase-orders/add/", PurchaseOrderCreateView.as_view(), name="po-create"),
    path("purchase-orders/<int:pk>/edit/", PurchaseOrderUpdateView.as_view(), name="po-update"),
    path("purchase-orders/<int:pk>/delete/", PurchaseOrderDeleteView.as_view(), name="po-delete"),
    path("purchase-order-lines/", PurchaseOrderLineListView.as_view(), name="line-list"),
    path("purchase-order-lines/add/", PurchaseOrderLineCreateView.as_view(), name="line-create"),
    path("purchase-order-lines/<int:pk>/edit/", PurchaseOrderLineUpdateView.as_view(), name="line-update"),
    path("purchase-order-lines/<int:pk>/delete/", PurchaseOrderLineDeleteView.as_view(), name="line-delete"),
    path("goods-receipts/", GoodsReceiptListView.as_view(), name="grn-list"),
    path("goods-receipts/add/", GoodsReceiptCreateView.as_view(), name="grn-create"),
    path("goods-receipts/<int:pk>/edit/", GoodsReceiptUpdateView.as_view(), name="grn-update"),
    path("goods-receipts/<int:pk>/delete/", GoodsReceiptDeleteView.as_view(), name="grn-delete"),
]

