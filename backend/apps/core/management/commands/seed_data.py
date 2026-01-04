"""
Seed data management command for NairaTrack
Creates demo categories, accounts, transactions, budgets, goals, and recurring
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import (
    Category, Account, Transaction, Budget, Goal, 
    GoalContribution, RecurringTransaction, Connection
)
from decimal import Decimal
from datetime import date, timedelta
import random
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the user'
        )
        parser.add_argument(
            '--auth0_id',
            type=str,
            help='Auth0 ID for the user'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        auth0_id = options.get('auth0_id')

        if not email and not auth0_id:
            # Default to test user if nothing provided
            email = 'test@example.com'
        
        user = None
        if auth0_id:
            try:
                user = User.objects.get(auth0_id=auth0_id)
                self.stdout.write(f'Found user by Auth0 ID: {auth0_id}')
            except User.DoesNotExist:
                pass
        
        if not user and email:
            # Create or get user by email
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Test',
                    'last_name': 'User',
                    'currency': 'NGN',
                    'timezone': 'Africa/Lagos',
                }
            )
            if created:
                user.set_password('testpassword123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created test user: {email}'))
            else:
                self.stdout.write(f'Using existing user: {email}')
        
        if not user:
             self.stdout.write(self.style.ERROR('User not found and could not be created'))
             return

        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Transaction.objects.filter(user=user).delete()
            Budget.objects.filter(user=user).delete()
            Goal.objects.filter(user=user).delete()
            RecurringTransaction.objects.filter(user=user).delete()
            Account.objects.filter(user=user).delete()
            Connection.objects.filter(user=user).delete()
            Category.objects.filter(user=user).delete()

        # Create system categories if they don't exist
        self.create_categories(user)
        
        # Create demo accounts
        accounts = self.create_accounts(user)
        
        # Create demo transactions
        self.create_transactions(user, accounts)
        
        # Create budgets
        self.create_budgets(user)
        
        # Create goals
        self.create_goals(user)
        
        # Create recurring transactions
        self.create_recurring(user, accounts)

        self.stdout.write(self.style.SUCCESS('✅ Seed data created successfully!'))

    def create_categories(self, user):
        """Create system categories"""
        expense_categories = [
            ('Food & Dining', '🍕', '#f97316'),
            ('Transportation', '🚗', '#3b82f6'),
            ('Shopping', '🛍️', '#ec4899'),
            ('Bills & Utilities', '💡', '#eab308'),
            ('Entertainment', '🎬', '#8b5cf6'),
            ('Healthcare', '🏥', '#ef4444'),
            ('Education', '📚', '#06b6d4'),
            ('Personal Care', '💅', '#f472b6'),
            ('Home', '🏠', '#14b8a6'),
            ('Travel', '✈️', '#0ea5e9'),
            ('Gifts & Donations', '🎁', '#a855f7'),
            ('Business', '💼', '#6366f1'),
            ('Fees & Charges', '🏦', '#64748b'),
            ('Cash Withdrawal', '💵', '#71717a'),
        ]
        
        income_categories = [
            ('Salary', '💰', '#10b981'),
            ('Freelance', '💻', '#06b6d4'),
            ('Investments', '📈', '#8b5cf6'),
            ('Gifts Received', '🎁', '#ec4899'),
            ('Refunds', '↩️', '#22c55e'),
            ('Other Income', '📥', '#64748b'),
        ]

        for name, icon, color in expense_categories + income_categories:
            Category.objects.get_or_create(
                name=name,
                is_system=True,
                defaults={'icon': icon, 'color': color}
            )
        
        self.stdout.write(f'Created {len(expense_categories) + len(income_categories)} categories')

    def create_accounts(self, user):
        """Create demo bank accounts"""
        # Create a connection first
        conn, _ = Connection.objects.get_or_create(
            user=user,
            institution_name='GTBank',
            defaults={
                'institution_logo': 'https://logo.clearbit.com/gtbank.com',
                'mono_id': f'demo_{uuid.uuid4().hex[:8]}',
                'status': 'connected',
            }
        )

        accounts_data = [
            ('GTBank Savings', 'savings', '****4521', 1250000),
            ('GTBank Current', 'current', '****8834', 450000),
            ('Access Bank', 'savings', '****2290', 780000),
        ]
        
        accounts = []
        for name, acc_type, masked, balance in accounts_data:
            account, _ = Account.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'connection': conn,
                    'type': acc_type,
                    'account_number_masked': masked,
                    'currency': 'NGN',
                    'balance': Decimal(balance),
                    'available_balance': Decimal(balance),
                    'mono_account_id': f'demo_{uuid.uuid4().hex[:8]}',
                }
            )
            accounts.append(account)
        
        self.stdout.write(f'Created {len(accounts)} accounts')
        return accounts

    def create_transactions(self, user, accounts):
        """Create demo transactions for the last 3 months"""
        if Transaction.objects.filter(user=user).exists():
            self.stdout.write('Transactions already exist, skipping...')
            return

        categories = {c.name: c for c in Category.objects.filter(is_system=True)}
        
        # Transaction templates
        expense_templates = [
            ('Shoprite', 'Groceries', 'Food & Dining', (8000, 25000)),
            ('Uber', 'Trip to work', 'Transportation', (1500, 5000)),
            ('Netflix', 'Subscription', 'Entertainment', (4400, 4400)),
            ('PHCN', 'Electricity bill', 'Bills & Utilities', (10000, 20000)),
            ('MTN Airtime', 'Data bundle', 'Bills & Utilities', (3000, 10000)),
            ('Chicken Republic', 'Lunch', 'Food & Dining', (2500, 6000)),
            ('Jumia', 'Online shopping', 'Shopping', (15000, 80000)),
            ('POS Withdrawal', 'Cash', 'Cash Withdrawal', (20000, 50000)),
            ('Spotify', 'Music subscription', 'Entertainment', (2900, 2900)),
            ('Bolt', 'Ride to meeting', 'Transportation', (2000, 4500)),
            ('Amazon Prime', 'Subscription', 'Entertainment', (3500, 3500)),
            ('Pharmacy', 'Medicine', 'Healthcare', (3000, 15000)),
            ('Kuda Bank', 'Transfer fee', 'Fees & Charges', (10, 50)),
        ]
        
        income_templates = [
            ('Salary - Tech Corp', 'January Salary', 'Salary', (650000, 650000)),
            ('Freelance Payment', 'Web design project', 'Freelance', (80000, 200000)),
            ('Refund - Jumia', 'Order refund', 'Refunds', (5000, 30000)),
        ]

        transactions = []
        today = date.today()
        
        # Generate transactions for the last 90 days
        for day_offset in range(90):
            tx_date = today - timedelta(days=day_offset)
            
            # 2-5 expense transactions per day
            for _ in range(random.randint(2, 5)):
                template = random.choice(expense_templates)
                merchant, desc, cat_name, amount_range = template
                amount = Decimal(random.randint(amount_range[0], amount_range[1]))
                
                transactions.append(Transaction(
                    user=user,
                    account=random.choice(accounts),
                    date=tx_date,
                    description=desc,
                    merchant_name=merchant,
                    amount=amount,
                    type='debit',
                    category=categories.get(cat_name),
                ))
            
            # Income - salary once a month, occasional freelance
            if tx_date.day == 25:  # Salary day
                template = income_templates[0]
                transactions.append(Transaction(
                    user=user,
                    account=accounts[0],
                    date=tx_date,
                    description=template[1],
                    merchant_name=template[0],
                    amount=Decimal(template[3][0]),
                    type='credit',
                    category=categories.get(template[2]),
                ))
            
            # Random freelance income
            if random.random() < 0.1:  # 10% chance
                template = income_templates[1]
                transactions.append(Transaction(
                    user=user,
                    account=random.choice(accounts),
                    date=tx_date,
                    description=template[1],
                    merchant_name=template[0],
                    amount=Decimal(random.randint(template[3][0], template[3][1])),
                    type='credit',
                    category=categories.get(template[2]),
                ))

        Transaction.objects.bulk_create(transactions)
        self.stdout.write(f'Created {len(transactions)} transactions')

    def create_budgets(self, user):
        """Create demo budgets"""
        if Budget.objects.filter(user=user).exists():
            self.stdout.write('Budgets already exist, skipping...')
            return

        categories = {c.name: c for c in Category.objects.filter(is_system=True)}
        
        budgets_data = [
            ('Food & Dining', 80000),
            ('Transportation', 40000),
            ('Entertainment', 30000),
            ('Bills & Utilities', 50000),
            ('Shopping', 25000),
            ('Healthcare', 20000),
        ]
        
        for cat_name, amount in budgets_data:
            category = categories.get(cat_name)
            if category:
                Budget.objects.create(
                    user=user,
                    category=category,
                    amount=Decimal(amount),
                    period='monthly',
                )
        
        self.stdout.write(f'Created {len(budgets_data)} budgets')

    def create_goals(self, user):
        """Create demo savings goals"""
        if Goal.objects.filter(user=user).exists():
            self.stdout.write('Goals already exist, skipping...')
            return

        goals_data = [
            ('Emergency Fund', '🏦', 1000000, 350000, date.today() + timedelta(days=180)),
            ('New Laptop', '💻', 500000, 125000, date.today() + timedelta(days=90)),
            ('Vacation Fund', '✈️', 300000, 50000, date.today() + timedelta(days=365)),
            ('New Phone', '📱', 200000, 180000, date.today() + timedelta(days=30)),
        ]
        
        for name, emoji, target, current, target_date in goals_data:
            goal = Goal.objects.create(
                user=user,
                name=name,
                emoji=emoji,
                target_amount=Decimal(target),
                current_amount=Decimal(current),
                target_date=target_date,
                status='active' if current < target else 'completed',
            )
            # Add some contribution history
            if current > 0:
                num_contributions = random.randint(3, 8)
                contribution_each = current / num_contributions
                for i in range(num_contributions):
                    GoalContribution.objects.create(
                        goal=goal,
                        amount=Decimal(contribution_each),
                        date=date.today() - timedelta(days=i * 7),
                    )
        
        self.stdout.write(f'Created {len(goals_data)} goals')

    def create_recurring(self, user, accounts):
        """Create demo recurring transactions"""
        if RecurringTransaction.objects.filter(user=user).exists():
            self.stdout.write('Recurring transactions already exist, skipping...')
            return

        categories = {c.name: c for c in Category.objects.filter(is_system=True)}
        today = date.today()
        
        recurring_data = [
            ('Netflix', '🎬', 4400, 'monthly', 5, 'Entertainment'),
            ('Spotify', '🎵', 2900, 'monthly', 10, 'Entertainment'),
            ('DSTV', '📺', 21000, 'monthly', 1, 'Entertainment'),
            ('Internet', '🌐', 12000, 'monthly', 15, 'Bills & Utilities'),
            ('Electricity', '💡', 15000, 'monthly', 20, 'Bills & Utilities'),
            ('Gym Membership', '🏋️', 25000, 'monthly', 1, 'Healthcare'),
            ('Rent', '🏠', 250000, 'yearly', 1, 'Home'),
        ]
        
        for name, icon, amount, freq, due_day, cat_name in recurring_data:
            next_date = today.replace(day=min(due_day, 28))
            if next_date <= today:
                if freq == 'monthly':
                    next_date = (next_date.replace(day=1) + timedelta(days=32)).replace(day=min(due_day, 28))
                elif freq == 'yearly':
                    next_date = next_date.replace(year=next_date.year + 1)
            
            RecurringTransaction.objects.create(
                user=user,
                name=name,
                icon=icon,
                amount=Decimal(amount),
                frequency=freq,
                next_date=next_date,
                category=categories.get(cat_name),
                account=accounts[0],
                status='active',
                reminder_days=3,
            )
        
        self.stdout.write(f'Created {len(recurring_data)} recurring transactions')
