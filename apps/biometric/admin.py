from django.contrib import admin

from .models import BiometricTemplate, BiometricVerificationLog


admin.site.register(BiometricTemplate)
admin.site.register(BiometricVerificationLog)
