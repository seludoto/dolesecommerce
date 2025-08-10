from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stores.models import StoreApplication


class Command(BaseCommand):
    help = 'Setup test data for store approval functionality - DISABLED to prevent password issues'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                'This command has been disabled to prevent password prompt issues.\n'
                'If you need test data, create it manually through the Django admin.'
            )
        )
        return

        # DISABLED CODE BELOW - Uncomment only if needed
        # # Create superuser
        # admin_user, created = User.objects.get_or_create(
        #     username='admin',
        #     defaults={
        #         'email': 'admin@example.com',
        #         'is_superuser': True,
        #         'is_staff': True,
        #         'first_name': 'Admin',
        #         'last_name': 'User'
        #     }
        # )
        # if created:
        #     admin_user.set_password('admin123')
        #     admin_user.save()
        #     self.stdout.write(self.style.SUCCESS('✅ Superuser created: admin/admin123'))
        # else:
        #     self.stdout.write(self.style.WARNING(f'ℹ️  Superuser already exists: {admin_user.username}'))

        # DISABLED - The rest of the test data creation code
        # # Create a test user for store application
        # test_user, created = User.objects.get_or_create(
        #     username='testuser',
        #     defaults={
        #         'email': 'testuser@example.com',
        #         'first_name': 'Test',
        #         'last_name': 'User'
        #     }
        # )
        # if created:
        #     test_user.set_password('test123')
        #     test_user.save()
        #     self.stdout.write(self.style.SUCCESS('✅ Test user created: testuser/test123'))
        # else:
        #     self.stdout.write(self.style.WARNING(f'ℹ️  Test user already exists: {test_user.username}'))

        # DISABLED - Store application creation code
        # # Create a test store application
        # application, created = StoreApplication.objects.get_or_create(
        #     user=test_user,
        #     defaults={
        #         'store_name': 'Test Electronics Store',
        #         'store_description': 'A test store selling electronics and gadgets',
        #         'business_type': 'electronics',
        #         'business_license': 'TEST123456',
        #         'tax_id': 'TAX789012',
        #         'contact_email': 'teststore@example.com',
        #         'contact_phone': '+1234567890',
        #         'business_address': '123 Test Street, Test City, Test Country',
        #         'status': 'pending'
        #     }
        # )
        # if created:
        #     self.stdout.write(self.style.SUCCESS(f'✅ Test store application created: {application.store_name}'))
        #     self.stdout.write(f'   - Status: {application.status}')
        #     self.stdout.write(f'   - User: {application.user.username}')
        #     self.stdout.write(f'   - Application ID: {application.id}')
        # else:
        #     self.stdout.write(self.style.WARNING(f'ℹ️  Store application already exists: {application.store_name}'))
        #     self.stdout.write(f'   - Status: {application.status}')
        #     self.stdout.write(f'   - Application ID: {application.id}')

        # self.stdout.write('\n🎯 Test Data Summary:')
        # self.stdout.write(f'   - Admin Panel: http://localhost:8000/admin/')
        # self.stdout.write(f'   - Login: admin/admin123')
        # self.stdout.write(f'   - Store Applications: http://localhost:8000/admin/stores/storeapplication/')
        # self.stdout.write(f'   - Test Application ID: {application.id}')
        # self.stdout.write('\n✨ Ready to test the approval button!')
