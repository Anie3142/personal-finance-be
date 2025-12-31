"""
Seed test data for NairaTrack development
Creates a test user with sample data: categories, accounts, transactions, budgets, goals, insights
"""
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import (
    User, Connection, Account, Category, Transaction,
    CategoryRule, Budget, Goal, GoalContribution,
    RecurringTransaction, Insight, Export
)


class Command(BaseCommand):
    help = 'Seeds the database with test data for development'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Starting seed process...')
        
        # Create test user
        user = self.create_test_user()
        
        # Create system categories
        categories = self.create_categories(user)
        
        # Create connections and accounts
        connection, accounts = self.create_accounts(user)
        
        # Create transactions
        self.create_transactions(user, accounts, categories)
        
        # Create budgets
        self.create_budgets(user, categories)
        
        # Create goals
        self.create_goals(user, accounts)
        
        # Create recurring transactions
        self.create_recurring(user, accounts, categories)
        
        # Create insights
        self.create_insights(user)
        
        self.stdout.write(self.style.SUCCESS('✅ Seed data created successfully!'))
        self.stdout.write(f'📧 Test user email: test@nairatrack.com')
        self.stdout.write(f'🔑 Test user password: testpassword123')

    def create_test_user(self):
        """Create or get test user"""
        user, created = User.objects.get_or_create(
            email='test@nairatrack.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'currency': 'NGN',
                'timezone': 'Africa/Lagos',
            }
        )
        if created:
            user.set_password('testpassword123')
            user.save()
            self.stdout.write(f'✅ Created test user: {user.email}')
        else:
            self.stdout.write(f'ℹ️  Test user already exists: {user.email}')
        return user

    def create_categories(self, user):
        """Create system categories"""
        expense_categories = [
            ('food', 'Food & Dining', '🍕', '#ef4444'),
            ('transport', 'Transportation', '🚗', '#f97316'),
            ('shopping', 'Shopping', '🛍️', '#8b5cf6'),
            ('bills', 'Bills & Utilities', '💡', '#eab308'),
            ('entertainment', 'Entertainment', '🎬', '#ec4899'),
            ('healthcare', 'Healthcare', '🏥', '#22c55e'),
            ('education', 'Education', '📚', '#3b82f6'),
            ('personal', 'Personal Care', '💅', '#f472b6'),
            ('home', 'Home', '🏠', '#14b8a6'),
            ('travel', 'Travel', '✈️', '#06b6d4'),
            ('gifts', 'Gifts & Donations', '🎁', '#a855f7'),
            ('business', 'Business', '💼', '#6366f1'),
            ('fees', 'Fees & Charges', '🏦', '#64748b'),
            ('uncategorized', 'Uncategorized', '❓', '#94a3b8'),
        ]
        
        income_categories = [
            ('salary', 'Salary', '💰', '#10b981'),
            ('freelance', 'Freelance', '💻', '#06b6d4'),
            ('investments', 'Investments', '📈', '#8b5cf6'),
            ('gifts_received', 'Gifts Received', '🎁', '#ec4899'),
            ('refunds', 'Refunds', '💵', '#22c55e'),
            ('other_income', 'Other Income', '📥', '#64748b'),
        ]
        
        categories = {}
        
        for slug, name, icon, color in expense_categories + income_categories:
            cat, created = Category.objects.get_or_create(
                name=name,
                is_system=True,
                defaults={
                    'icon': icon,
                    'color': color,
                    'user': None,  # System categories have no user
                }
            )
            categories[slug] = cat
            if created:
                self.stdout.write(f'  ✅ Created category: {name}')
        
        return categories

    def create_accounts(self, user):
        """Create sample bank connections and accounts"""
        # Create connection (simulating Mono connection)
        connection, _ = Connection.objects.get_or_create(
            user=user,
            institution_name='GTBank',
            defaults={
                'mono_id': 'test_mono_id_gtbank',
                'institution_logo': 'https://mono.co/banks/gtbank.png',
                'status': 'connected',
                'last_synced_at': timezone.now(),
            }
        )
        
        # Create accounts
        accounts = []
        
        account_data = [
            ('GTBank Savings', 'savings', '1234', 1500000_00),  # ₦1.5M in kobo
            ('GTBank Current', 'current', '5678', 350000_00),   # ₦350K in kobo
            ('Access Salary', 'savings', '9012', 850000_00),    # ₦850K in kobo
        ]
        
        for name, acc_type, last_four, balance in account_data:
            account, created = Account.objects.get_or_create(
                user=user,
                name=name,
                defaults={
                    'connection': connection,
                    'type': acc_type,
                    'account_number_masked': f'****{last_four}',
                    'currency': 'NGN',
                    'balance': balance,
                    'available_balance': balance,
                    'last_synced_at': timezone.now(),
                }
            )
            accounts.append(account)
            if created:
                self.stdout.write(f'  ✅ Created account: {name}')
        
        return connection, accounts

    def create_transactions(self, user, accounts, categories):
        """Create sample transactions for the last 3 months"""
        if Transaction.objects.filter(user=user).exists():
            self.stdout.write('  ℹ️  Transactions already exist, skipping...')
            return
        
        merchants = {
            'food': ['Shoprite', 'Chicken Republic', 'Dominos Pizza', 'KFC', 'The Place'],
            'transport': ['Uber', 'Bolt', 'Shell Fuel', 'Oando Fuel', 'Lagos BRT'],
            'shopping': ['Jumia', 'Konga', 'Zara', 'Nike Store', 'Apple Store'],
            'bills': ['IKEDC', 'MTN', 'DSTV', 'Netflix', 'Spotify'],
            'entertainment': ['Filmhouse Cinemas', 'Genesis Cinemas', 'Steam', 'PlayStation'],
            'healthcare': ['MedPlus Pharmacy', 'Reddington Hospital', 'EyeFoundation'],
        }
        
        transactions = []
        today = timezone.now().date()
        
        # Generate transactions for the last 90 days
        for day_offset in range(90):
            date = today - timedelta(days=day_offset)
            
            # 2-5 transactions per day
            num_transactions = random.randint(2, 5)
            
            for _ in range(num_transactions):
                # Random category (weighted towards common ones)
                category_slug = random.choices(
                    ['food', 'transport', 'shopping', 'bills', 'entertainment', 'healthcare'],
                    weights=[30, 25, 15, 15, 10, 5]
                )[0]
                
                category = categories.get(category_slug)
                merchant_list = merchants.get(category_slug, ['Unknown Merchant'])
                merchant = random.choice(merchant_list)
                
                # Random amount (in kobo)
                amount = random.randint(500_00, 50000_00)  # ₦500 to ₦50,000
                
                transactions.append(Transaction(
                    user=user,
                    account=random.choice(accounts),
                    date=date,
                    description=f'POS - {merchant}',
                    merchant_name=merchant,
                    amount=amount,
                    type='debit',
                    category=category,
                    notes='',
                    is_recurring=False,
                ))
        
        # Add monthly salary (income)
        for month_offset in range(3):
            salary_date = today.replace(day=25) - timedelta(days=month_offset * 30)
            if salary_date <= today:
                transactions.append(Transaction(
                    user=user,
                    account=accounts[2] if len(accounts) > 2 else accounts[0],
                    date=salary_date,
                    description='SALARY CREDIT - NAMELESS COMPANY LTD',
                    merchant_name='Nameless Company Ltd',
                    amount=650000_00,  # ₦650K
                    type='credit',
                    category=categories.get('salary'),
                    notes='Monthly salary',
                    is_recurring=True,
                ))
        
        Transaction.objects.bulk_create(transactions)
        self.stdout.write(f'  ✅ Created {len(transactions)} transactions')

    def create_budgets(self, user, categories):
        """Create sample budgets"""
        if Budget.objects.filter(user=user).exists():
            self.stdout.write('  ℹ️  Budgets already exist, skipping...')
            return
        
        budget_data = [
            ('food', 80000_00),        # ₦80K
            ('transport', 50000_00),   # ₦50K
            ('shopping', 35000_00),    # ₦35K
            ('bills', 45000_00),       # ₦45K
            ('entertainment', 20000_00), # ₦20K
            ('healthcare', 15000_00),  # ₦15K
        ]
        
        budgets = []
        for cat_slug, amount in budget_data:
            category = categories.get(cat_slug)
            if category:
                budgets.append(Budget(
                    user=user,
                    category=category,
                    amount=amount,
                    period='monthly',
                    rollover=False,
                ))
        
        Budget.objects.bulk_create(budgets)
        self.stdout.write(f'  ✅ Created {len(budgets)} budgets')

    def create_goals(self, user, accounts):
        """Create sample savings goals"""
        if Goal.objects.filter(user=user).exists():
            self.stdout.write('  ℹ️  Goals already exist, skipping...')
            return
        
        goals_data = [
            ('Emergency Fund', '🛡️', 1000000_00, 450000_00, 180),   # ₦1M target, ₦450K saved
            ('New MacBook', '💻', 2500000_00, 1200000_00, 120),     # ₦2.5M target, ₦1.2M saved
            ('Vacation to Dubai', '✈️', 3000000_00, 500000_00, 365), # ₦3M target, ₦500K saved
        ]
        
        for name, emoji, target, current, days_to_target in goals_data:
            goal = Goal.objects.create(
                user=user,
                name=name,
                emoji=emoji,
                target_amount=target,
                current_amount=current,
                target_date=timezone.now().date() + timedelta(days=days_to_target),
                status='active',
            )
            
            # Add some contributions
            for i in range(5):
                contribution_date = timezone.now().date() - timedelta(days=i * 15)
                GoalContribution.objects.create(
                    goal=goal,
                    amount=current // 5,
                    date=contribution_date,
                )
        
        self.stdout.write(f'  ✅ Created {len(goals_data)} goals with contributions')

    def create_recurring(self, user, accounts, categories):
        """Create sample recurring transactions"""
        if RecurringTransaction.objects.filter(user=user).exists():
            self.stdout.write('  ℹ️  Recurring transactions already exist, skipping...')
            return
        
        recurring_data = [
            ('Netflix Subscription', 4400_00, 'monthly', 'entertainment'),
            ('Spotify Premium', 2500_00, 'monthly', 'entertainment'),
            ('DSTV Premium', 24500_00, 'monthly', 'bills'),
            ('MTN Data', 5000_00, 'monthly', 'bills'),
            ('Gym Membership', 25000_00, 'monthly', 'healthcare'),
        ]
        
        recurring = []
        for name, amount, frequency, cat_slug in recurring_data:
            category = categories.get(cat_slug)
            recurring.append(RecurringTransaction(
                user=user,
                name=name,
                amount=amount,
                frequency=frequency,
                next_date=timezone.now().date() + timedelta(days=random.randint(1, 28)),
                category=category,
                account=accounts[0] if accounts else None,
                status='active',
                reminder_days=3,
            ))
        
        RecurringTransaction.objects.bulk_create(recurring)
        self.stdout.write(f'  ✅ Created {len(recurring)} recurring transactions')

    def create_insights(self, user):
        """Create sample insights"""
        if Insight.objects.filter(user=user).exists():
            self.stdout.write('  ℹ️  Insights already exist, skipping...')
            return
        
        insights_data = [
            ('spending_decrease', 'Great job on Food! 📉', 'You spent 23% less on Food & Dining this month compared to last month.', 'success'),
            ('budget_warning', 'Shopping budget alert ⚠️', 'Your Shopping budget is 108% used with 10 days left in the month.', 'warning'),
            ('upcoming_bill', 'Netflix due soon 🔔', 'Your Netflix subscription of ₦4,400 is due in 5 days.', 'info'),
            ('goal_progress', 'MacBook goal milestone! 🎯', "You're 48% of the way to your New MacBook goal. Keep going!", 'success'),
        ]
        
        insights = []
        for insight_type, title, message, severity in insights_data:
            insights.append(Insight(
                user=user,
                type=insight_type,
                title=title,
                message=message,
                severity=severity,
                data={},
                dismissed=False,
            ))
        
        Insight.objects.bulk_create(insights)
        self.stdout.write(f'  ✅ Created {len(insights)} insights')
