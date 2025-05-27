from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from apps.brain.models import ProcessingJob
import tempfile
import os


class Command(BaseCommand):
    help = 'Test the file upload and processing workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to test file (optional)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧠 Testing Brain File Upload Workflow'))
        self.stdout.write('=' * 50)

        # Create test user
        user, created = User.objects.get_or_create(
            username='test_brain_user',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created test user: {user.username}'))
        else:
            self.stdout.write(f'✓ Using existing user: {user.username}')

        # Test file upload
        self.test_file_upload(user, options.get('file'))

        # List recent jobs
        self.list_recent_jobs()

    def test_file_upload(self, user, file_path=None):
        """Test file upload functionality"""
        self.stdout.write('\n📤 Testing File Upload...')

        # Create test file if none provided
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            file_name = os.path.basename(file_path)
        else:
            # Create a simple test document
            file_content = b"""
            Sample Document for Testing
            
            This is a test document that contains some sample text for question generation.
            The brain engine should be able to extract this text and generate meaningful questions.
            
            Key points:
            1. This is the first important point
            2. This is the second important point  
            3. This is the third important point
            
            The system should be able to process this content and create questions about these topics.
            """
            file_name = 'test_document.txt'

        # Create Django test client
        client = Client()
        client.force_login(user)

        # Create uploaded file
        uploaded_file = SimpleUploadedFile(
            file_name,
            file_content,
            content_type="text/plain"
        )

        # Test the upload
        response = client.post('/app/api/process-document/', {
            'document': uploaded_file,
            'language': 'auto',
            'question_type': 'MULTIPLECHOICE',
            'num_questions': 3
        })

        self.stdout.write(f'Response Status: {response.status_code}')

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    job_id = data.get('job_id')
                    questions_count = data.get('questions_generated', 0)
                    
                    self.stdout.write(self.style.SUCCESS(f'✓ Upload successful!'))
                    self.stdout.write(f'  Job ID: {job_id}')
                    self.stdout.write(f'  Questions Generated: {questions_count}')

                    # Get job details
                    try:
                        job = ProcessingJob.objects.get(id=job_id)
                        self.stdout.write(f'  Status: {job.status}')
                        self.stdout.write(f'  File: {job.document_file}')
                        
                        if job.status == 'completed':
                            qa_pairs = job.get_qa_pairs()
                            self.stdout.write(f'  Q&A Pairs in DB: {qa_pairs.count()}')
                            
                            # Show first question
                            if qa_pairs.exists():
                                first_qa = qa_pairs.first()
                                self.stdout.write(f'  Sample Question: {first_qa.question[:100]}...')
                        
                    except ProcessingJob.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'❌ Job {job_id} not found'))

                else:
                    error = data.get('error', 'Unknown error')
                    self.stdout.write(self.style.ERROR(f'❌ Upload failed: {error}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to parse response: {e}'))
                self.stdout.write(f'Raw response: {response.content.decode()[:200]}...')
        
        else:
            self.stdout.write(self.style.ERROR(f'❌ Request failed: {response.status_code}'))
            self.stdout.write(f'Response: {response.content.decode()[:200]}...')

    def list_recent_jobs(self):
        """List recent processing jobs"""
        self.stdout.write('\n📋 Recent Processing Jobs:')
        self.stdout.write('-' * 30)

        jobs = ProcessingJob.objects.all().order_by('-created_at')[:5]
        
        if not jobs:
            self.stdout.write('No jobs found')
            return

        for job in jobs:
            status_color = {
                'completed': self.style.SUCCESS,
                'failed': self.style.ERROR,
                'processing': self.style.WARNING,
                'pending': self.style.NOTICE
            }.get(job.status, self.style.NOTICE)

            self.stdout.write(f'Job #{job.id}: {job.document_name}')
            self.stdout.write(f'  Status: {status_color(job.status)}')
            self.stdout.write(f'  Created: {job.created_at}')
            
            if job.status == 'completed':
                qa_count = job.get_qa_pairs().count()
                self.stdout.write(f'  Questions: {qa_count}')
            elif job.status == 'failed':
                self.stdout.write(f'  Error: {job.error_message[:100]}...')
            
            self.stdout.write('')
