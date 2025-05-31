from django.contrib import admin
from .models import EmailOTP, OTPRateLimit

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'created_at', 'expires_at', 'is_verified', 'attempts', 'ip_address']
    list_filter = ['is_verified', 'created_at', 'expires_at']
    search_fields = ['user__username', 'email', 'ip_address']
    readonly_fields = ['created_at', 'expires_at', 'otp_hash']
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(OTPRateLimit)
class OTPRateLimitAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'attempts', 'first_attempt', 'last_attempt', 'is_blocked', 'blocked_until']
    list_filter = ['is_blocked', 'first_attempt', 'last_attempt']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['first_attempt', 'last_attempt']
    ordering = ['-last_attempt']
