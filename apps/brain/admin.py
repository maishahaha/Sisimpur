from django.contrib import admin
from .models import ProcessingJob, QuestionAnswer

@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'document_name', 'status', 'language', 'created_at', 'completed_at']
    list_filter = ['status', 'language', 'created_at']
    search_fields = ['document_name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'document_name', 'status', 'language')
        }),
        ('Processing Details', {
            'fields': ('num_questions', 'question_type', 'document_type', 'is_question_paper')
        }),
        ('Files', {
            'fields': ('document_file', 'extracted_text_file', 'output_file')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )

@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'job', 'question_preview', 'question_type', 'created_at']
    list_filter = ['question_type', 'created_at']
    search_fields = ['question', 'answer', 'job__document_name']
    readonly_fields = ['created_at']
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question Preview'
