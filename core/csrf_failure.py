from django.contrib import messages
from django.shortcuts import redirect
from django.views.csrf import csrf_failure as django_csrf_failure


def csrf_failure(request, reason=""):
    if request.path.startswith("/accounts/login/") and request.method == "POST":
        messages.error(request, "Sessão expirada. Tente entrar novamente.")
        return redirect("/accounts/login/")
    return django_csrf_failure(request, reason=reason)

