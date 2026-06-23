from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Blog, Inquiry, Customer
import json, sqlite3, os, logging

logger = logging.getLogger(__name__)

@csrf_exempt
def api_form_submission(request):
    """JSON API endpoint for registration form submissions.
    Also writes to feishu-backup SQLite for dual-write."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    country  = data.get("country", "")
    name     = data.get("name", "")
    email    = data.get("email", "")
    whatsapp = data.get("whatsapp", "")
    message  = data.get("message", "")

    if not email or not name:
        return JsonResponse({"error": "name and email required"}, status=400)

    # 1) Save to Django models (Customer + Inquiry)
    try:
        customer, _ = Customer.objects.get_or_create(
            email=email,
            defaults={
                "company_name": name,
                "contact_person": name,
                "phone": whatsapp,
                "country": country,
                "source": "web-registration",
            },
        )
        Inquiry.objects.create(
            customer=customer,
            message=message,
            quantity="",
            target_price="",
        )
    except Exception as e:
        logger.error("Django save error: %s", e)

    # 2) Dual-write to feishu-backup SQLite
    try:
        db_path = os.path.expanduser("~/.hermes/data/trade.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO trade_records
               (customer_name, customer_contact, product_type, quantity_kg, notes, source)
               VALUES (?, ?, 'inquiry', 0, ?, 'web')""",
            (name, f"{email} / {whatsapp} / {country}", message[:500]),
        )
        # Also add customer record
        conn.execute(
            """INSERT OR IGNORE INTO customers (name, email, whatsapp, country, source)
               VALUES (?, ?, ?, ?, 'web')""",
            (name, email, whatsapp, country),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("SQLite dual-write error: %s", e)

    return JsonResponse({"status": "ok", "message": "Inquiry received"})

def home(request):
    products = Product.objects.filter(is_active=True)[:6]
    blogs = Blog.objects.filter(is_published=True)[:3]
    return render(request, "index.html", {"products": products, "blogs": blogs})

def products(request):
    prods = Product.objects.filter(is_active=True)
    return render(request, "products/index.html", {"products": prods})

def product_detail(request, pk):
    p = get_object_or_404(Product, pk=pk)
    return render(request, "products/detail.html", {"product": p})

def about(request):
    return render(request, "about/index.html")

def contact(request):
    if request.method == "POST":
        try:
            customer, _ = Customer.objects.get_or_create(
                email=request.POST.get("email",""),
                defaults={"company_name": request.POST.get("company",""), "contact_person": request.POST.get("name",""), "phone": request.POST.get("phone",""), "market": request.POST.get("market","usa")}
            )
            Inquiry.objects.create(customer=customer, message=request.POST.get("message",""), quantity=request.POST.get("quantity",""))
            messages.success(request, "Inquiry submitted! We will contact you within 24 hours.")
        except Exception as e:
            messages.error(request, f"Error: {e}")
        return HttpResponseRedirect(reverse("contact"))
    return render(request, "contact/index.html")

def blog(request):
    blogs = Blog.objects.filter(is_published=True)
    return render(request, "blog/index.html", {"blogs": blogs})

def blog_detail(request, pk):
    b = get_object_or_404(Blog, pk=pk)
    return render(request, "blog/detail.html", {"blog": b})

# Japanese
def jp_home(request):
    products = Product.objects.filter(is_active=True)[:6]
    blogs = Blog.objects.filter(is_published=True)[:3]
    return render(request, "jp/index.html", {"products": products, "blogs": blogs})

def jp_products(request):
    prods = Product.objects.filter(is_active=True)
    return render(request, "jp/products/index.html", {"products": prods})

def jp_about(request):
    return render(request, "jp/about/index.html")

def jp_contact(request):
    if request.method == "POST":
        customer, _ = Customer.objects.get_or_create(
            email=request.POST.get("email",""),
            defaults={"company_name": request.POST.get("company",""), "contact_person": request.POST.get("name",""), "phone": request.POST.get("phone",""), "market": "japan"}
        )
        Inquiry.objects.create(customer=customer, message=request.POST.get("message",""))
        messages.success(request, "Thank you! We will contact you within 24 hours.")
        return HttpResponseRedirect(reverse("jp_contact"))
    return render(request, "jp/contact/index.html")

def jp_blog(request):
    blogs = Blog.objects.filter(is_published=True)
    return render(request, "jp/blog/index.html", {"blogs": blogs})
