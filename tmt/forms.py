from pathlib import Path
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Collection, Deck

User = get_user_model()


class DeckUploadForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = [
            "title", "description", "original_file", "visibility",
            "source_title", "source_author", "source_publisher", "source_url", "copyright_notice",
            "allowed_groups", "allowed_users",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "copyright_notice": forms.TextInput(attrs={"placeholder": "例如：Third-party copyrighted material"}),
            "allowed_groups": forms.SelectMultiple(attrs={"size": 5}),
            "allowed_users": forms.SelectMultiple(attrs={"size": 5}),
        }

    def clean_original_file(self):
        f = self.cleaned_data["original_file"]
        ext = Path(f.name).suffix.lower()
        if ext not in settings.TMT_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(f"僅允許：{', '.join(settings.TMT_ALLOWED_EXTENSIONS)}")
        max_bytes = settings.TMT_MAX_UPLOAD_MB * 1024 * 1024
        if f.size > max_bytes:
            raise forms.ValidationError(f"檔案不可超過 {settings.TMT_MAX_UPLOAD_MB} MB")
        return f

    def clean(self):
        cleaned = super().clean()
        visibility = cleaned.get("visibility")
        if visibility in {Deck.Visibility.RESTRICTED, Deck.Visibility.CONFIDENTIAL}:
            if not cleaned.get("allowed_groups") and not cleaned.get("allowed_users"):
                self.add_error("allowed_users", "限制/機密簡報至少要指定一位使用者或一個群組。")
        return cleaned


class DeckEditForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = [
            "title", "description", "visibility",
            "source_title", "source_author", "source_publisher", "source_url", "copyright_notice",
            "allowed_groups", "allowed_users",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "allowed_groups": forms.SelectMultiple(attrs={"size": 5}),
            "allowed_users": forms.SelectMultiple(attrs={"size": 5}),
        }

    def clean(self):
        cleaned = super().clean()
        visibility = cleaned.get("visibility")
        if visibility in {Deck.Visibility.RESTRICTED, Deck.Visibility.CONFIDENTIAL}:
            if not cleaned.get("allowed_groups") and not cleaned.get("allowed_users"):
                self.add_error("allowed_users", "限制/機密簡報至少要指定一位使用者或一個群組。")
        return cleaned


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
