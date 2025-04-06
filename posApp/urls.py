from . import views, reports_views, report_views2
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic.base import RedirectView

#app_name = "posApp"
urlpatterns = [
    path('redirect-admin', RedirectView.as_view(url="/admin"),name="redirect-admin"),
    path('', views.home, name="home-page"),
    path('login', auth_views.LoginView.as_view(template_name = 'posApp/login.html',redirect_authenticated_user=True), name="login"),
    path('userlogin', views.login_user, name="login-user"),
    path('logout', views.logoutuser, name="logout"),
    path('category', views.category, name="category-page"),
    path('manage_category', views.manage_category, name="manage_category-page"),
    path('save_category', views.save_category, name="save-category-page"),
    path('delete_category', views.delete_category, name="delete-category"),
    path('products', views.products, name="product-page"),
    path('manage_products', views.manage_products, name="manage_products-page"),
    path('test', views.test, name="test-page"),
    path('save_product', views.save_product, name="save-product-page"),
    path('delete_product', views.delete_product, name="delete-product"),
    path('pos', views.pos, name="pos-page"),
    path('checkout-modal', views.checkout_modal, name="checkout-modal"),
    path('save-pos', views.save_pos, name="save-pos"),
    path('sales', views.salesList, name="sales-page"),
    path('receipt', views.receipt, name="receipt-modal"),
    path('delete_sale', views.delete_sale, name="delete-sale"),
    path('get_measurements/<int:category_id>/', views.get_measurements, name="get_measurements"),
    path('reports', views.reports, name="reports-page"),
    path('generate_report', views.generate_report, name="generate_report"),
    path('get_report/<int:id>/', views.get_report, name="get_report"),
    path('delete_report', views.delete_report, name="delete_report"),
    path("get_product_json", views.get_product_json, name="get_product_json"),
    
    # path('employees', views.employees, name="employee-page"),
    # path('manage_employees', views.manage_employees, name="manage_employees-page"),
    # path('save_employee', views.save_employee, name="save-employee-page"),
    # path('delete_employee', views.delete_employee, name="delete-employee"),
    # path('view_employee', views.view_employee, name="view-employee-page"),
    
    path("payment/callback", views.payment_callback, name="payment_callback"),
    path("payment/confirmation", views.payment_confirmation, name="payment_confirmation"),
    path("payment/validation", views.payment_validation, name="payment_validation"),
    path("payment/result", views.payment_result, name="payment_result"),
    path("payment/timeout", views.payment_timeout, name="payment_timeout"),
    path('payment/check', views.check_payment, name="check_payment"),
    
    path('reports_view', views.reports_view, name="reports_view"),
    path('reports_data', report_views2.reports_data, name="reports_data"),
    path('chart_detail', report_views2.chart_detail, name="chart_detail"),
]