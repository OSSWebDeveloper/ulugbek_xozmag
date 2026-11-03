"""Xodimning login va parolini xavfsiz o'zgartirish."""
from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render


def boshlangich_parol(user):
    """Standart parol bilan kirgan hisob birinchi kirishda uni o'zgartirsin."""
    return user.is_authenticated and user.username in ("server", "kassa") and user.check_password(user.username)


class HisobForm(forms.Form):
    username = forms.CharField(label="Yangi login", max_length=150)
    old_password = forms.CharField(label="Hozirgi parol", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Yangi parol", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Yangi parolni takrorlang", widget=forms.PasswordInput)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["username"].initial = user.username
        for field in self.fields.values():
            field.widget.attrs["class"] = "kirish"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_username(self):
        from django.contrib.auth import get_user_model
        value = self.cleaned_data["username"].strip()
        if not value:
            raise forms.ValidationError("Login bo'sh bo'lishi mumkin emas.")
        if get_user_model().objects.filter(username__iexact=value).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Bu login band.")
        return value

    def clean_old_password(self):
        password = self.cleaned_data["old_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("Hozirgi parol noto'g'ri.")
        return password

    def clean(self):
        values = super().clean()
        first, second = values.get("new_password1"), values.get("new_password2")
        if first and second and first != second:
            self.add_error("new_password2", "Parollar bir xil emas.")
        if first:
            if first in ("server", "kassa") or first == values.get("username"):
                self.add_error("new_password1", "Standart login/paroldan foydalanmang.")
            elif self.user.check_password(first):
                self.add_error("new_password1", "Yangi parol eskisidan farq qilishi kerak.")
            else:
                try:
                    validate_password(first, self.user)
                except ValidationError as exc:
                    self.add_error("new_password1", exc)
        return values


@login_required
def sozlamalar(request):
    majburiy = boshlangich_parol(request.user)
    form = HisobForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        user = request.user
        user.username = form.cleaned_data["username"]
        user.set_password(form.cleaned_data["new_password1"])
        user.save(update_fields=["username", "password"])
        update_session_auth_hash(request, user)
        messages.success(request, "Login va parol muvaffaqiyatli o'zgartirildi.")
        return redirect("qarz:boshlash")
    return render(request, "akkaunt/sozlamalar.html", {"form": form, "majburiy": majburiy})
