from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.products, name="products"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("blog/", views.blog, name="blog"),
    path("blog/<int:pk>/", views.blog_detail, name="blog_detail"),
    path("jp/", views.jp_home, name="jp_home"),
    path("jp/products/", views.jp_products, name="jp_products"),
    path("jp/about/", views.jp_about, name="jp_about"),
    path("jp/contact/", views.jp_contact, name="jp_contact"),
    path("jp/blog/", views.jp_blog, name="jp_blog"),
]
