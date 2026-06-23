from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    CATEGORY_CHOICES = [
        ("bar", "Silver Bar / 银锭"),
    ]
    name_en = models.CharField(max_length=200, verbose_name="名称(EN)")
    name_jp = models.CharField(max_length=200, blank=True, verbose_name="名称(JP)")
    name_cn = models.CharField(max_length=200, blank=True, verbose_name="名称(CN)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="分类")
    purity = models.CharField(max_length=50, verbose_name="纯度")
    specs = models.TextField(blank=True, verbose_name="规格")
    description_en = models.TextField(verbose_name="描述(EN)")
    description_jp = models.TextField(blank=True, verbose_name="描述(JP)")
    moq = models.CharField(max_length=100, blank=True, verbose_name="最小起订量")
    price_range = models.CharField(max_length=200, blank=True, verbose_name="价格区间")
    is_active = models.BooleanField(default=True, verbose_name="上架")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "产品"
        verbose_name_plural = "产品管理"
        ordering = ["sort_order"]
    def __str__(self):
        return self.name_en

class Customer(models.Model):
    company_name = models.CharField(max_length=200, verbose_name="公司名称")
    contact_person = models.CharField(max_length=100, verbose_name="联系人")
    email = models.EmailField(verbose_name="邮箱")
    phone = models.CharField(max_length=50, blank=True, verbose_name="电话/WhatsApp")
    country = models.CharField(max_length=100, blank=True, verbose_name="国家")
    market = models.CharField(max_length=20, choices=[("usa","USA"),("japan","Japan"),("other","Other")], default="usa", verbose_name="目标市场")
    notes = models.TextField(blank=True, verbose_name="备注")
    source = models.CharField(max_length=100, blank=True, verbose_name="来源")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "客户"
        verbose_name_plural = "客户管理"
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.company_name} - {self.contact_person}"

class Inquiry(models.Model):
    STATUS_CHOICES = [
        ("new", "New / 新询价"),
        ("quoted", "Quoted / 已报价"),
        ("negotiating", "Negotiating / 洽谈中"),
        ("converted", "Converted / 已转订单"),
        ("closed", "Closed / 已关闭"),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="inquiries", verbose_name="客户")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="产品")
    quantity = models.CharField(max_length=100, blank=True, verbose_name="需求量")
    target_price = models.CharField(max_length=100, blank=True, verbose_name="目标价")
    delivery_location = models.CharField(max_length=200, blank=True, verbose_name="交货地")
    message = models.TextField(verbose_name="询价内容")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="状态")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="负责人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "询价"
        verbose_name_plural = "询价管理"
        ordering = ["-created_at"]
    def __str__(self):
        return f"Inquiry #{self.id} - {self.customer.company_name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending / 待确认"),
        ("confirmed", "Confirmed / 已确认"),
        ("paid", "Paid / 已付款"),
        ("shipped", "Shipped / 已发货"),
        ("delivered", "Delivered / 已送达"),
        ("cancelled", "Cancelled / 已取消"),
    ]
    PAYMENT_CHOICES = [("tt", "TT / 电汇"), ("lc", "LC / 信用证")]
    order_no = models.CharField(max_length=50, unique=True, verbose_name="订单号")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders", verbose_name="客户")
    inquiry = models.ForeignKey(Inquiry, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="来源询价")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="产品")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="数量(kg)")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="单价(USD/kg)")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="总金额(USD)")
    payment_term = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="tt", verbose_name="支付方式")
    delivery_term = models.CharField(max_length=100, default="FOB Hong Kong", verbose_name="交货条款")
    delivery_port = models.CharField(max_length=200, blank=True, verbose_name="目的港")
    shipping_method = models.CharField(max_length=50, blank=True, verbose_name="运输方式")
    etd = models.DateField(null=True, blank=True, verbose_name="预计发货日")
    eta = models.DateField(null=True, blank=True, verbose_name="预计到货日")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态")
    notes = models.TextField(blank=True, verbose_name="备注")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="负责人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单管理"
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.order_no} - {self.customer.company_name}"

class Blog(models.Model):
    title_en = models.CharField(max_length=300, verbose_name="标题(EN)")
    title_jp = models.CharField(max_length=300, blank=True, verbose_name="标题(JP)")
    summary_en = models.TextField(verbose_name="摘要(EN)")
    summary_jp = models.TextField(blank=True, verbose_name="摘要(JP)")
    content_en = models.TextField(blank=True, verbose_name="内容(EN)")
    content_jp = models.TextField(blank=True, verbose_name="内容(JP)")
    category = models.CharField(max_length=100, blank=True, verbose_name="分类")
    is_published = models.BooleanField(default=False, verbose_name="发布")
    published_at = models.DateField(null=True, blank=True, verbose_name="发布日期")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "博客管理"
        ordering = ["-published_at"]
    def __str__(self):
        return self.title_en
