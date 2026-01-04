"""API Views for NairaTrack"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
from .models import *
from .serializers import *


# Health Check - Public endpoint
class HealthCheckView(views.APIView):
    """Health check endpoint for load balancers and monitoring"""
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })


# Auth Views
class UserMeView(views.APIView):
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'currency': user.currency,
            'timezone': user.timezone,
            'created_at': user.date_joined.isoformat()
        })
    
    def patch(self, request):
        user = request.user
        for field in ['first_name', 'last_name', 'currency', 'timezone']:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return self.get(request)


# Account Views
class AccountListView(views.APIView):
    def get(self, request):
        accounts = Account.objects.filter(user=request.user)
        account_type = request.query_params.get('type')
        if account_type:
            accounts = accounts.filter(type=account_type)
        return Response({'accounts': AccountSerializer(accounts, many=True).data})


class AccountDetailView(views.APIView):
    def get(self, request, pk):
        try:
            account = Account.objects.get(pk=pk, user=request.user)
            return Response(AccountSerializer(account).data)
        except Account.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


# Transaction Views
class TransactionListView(views.APIView):
    def get(self, request):
        txns = Transaction.objects.filter(user=request.user)
        
        if request.query_params.get('account_id'):
            txns = txns.filter(account_id=request.query_params['account_id'])
        if request.query_params.get('category_id'):
            txns = txns.filter(category_id=request.query_params['category_id'])
        if request.query_params.get('type'):
            txns = txns.filter(type=request.query_params['type'])
        if request.query_params.get('from'):
            txns = txns.filter(date__gte=request.query_params['from'])
        if request.query_params.get('to'):
            txns = txns.filter(date__lte=request.query_params['to'])
        if request.query_params.get('search'):
            txns = txns.filter(description__icontains=request.query_params['search'])
        
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 50))
        total = txns.count()
        txns = txns[(page-1)*limit:page*limit]
        
        return Response({
            'transactions': TransactionSerializer(txns, many=True).data,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': total > page * limit
        })


class TransactionDetailView(views.APIView):
    def get(self, request, pk):
        try:
            txn = Transaction.objects.get(pk=pk, user=request.user)
            return Response(TransactionSerializer(txn).data)
        except Transaction.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def patch(self, request, pk):
        try:
            txn = Transaction.objects.get(pk=pk, user=request.user)
            for field in ['category_id', 'notes', 'is_recurring']:
                if field in request.data:
                    if field == 'category_id':
                        txn.category_id = request.data[field]
                    else:
                        setattr(txn, field, request.data[field])
            txn.save()
            return Response(TransactionSerializer(txn).data)
        except Transaction.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class BulkCategorizeView(views.APIView):
    def post(self, request):
        ids = request.data.get('transaction_ids', [])
        category_id = request.data.get('category_id')
        updated = Transaction.objects.filter(user=request.user, id__in=ids).update(category_id=category_id)
        return Response({'updated_count': updated})


class ManualTransactionView(views.APIView):
    def post(self, request):
        data = request.data
        txn = Transaction.objects.create(
            user=request.user,
            account_id=data['account_id'],
            date=data['date'],
            description=data['description'],
            amount=data['amount'],
            type=data['type'],
            category_id=data.get('category_id'),
            notes=data.get('notes', '')
        )
        return Response(TransactionSerializer(txn).data, status=201)


# Category Views
class CategoryListView(views.APIView):
    def get(self, request):
        cats = Category.objects.filter(user=request.user) | Category.objects.filter(is_system=True)
        return Response({'categories': CategorySerializer(cats, many=True).data})
    
    def post(self, request):
        cat = Category.objects.create(
            user=request.user,
            name=request.data['name'],
            icon=request.data['icon'],
            color=request.data['color'],
            parent_id=request.data.get('parent_id')
        )
        return Response(CategorySerializer(cat).data, status=201)


class CategoryDetailView(views.APIView):
    def patch(self, request, pk):
        try:
            cat = Category.objects.get(pk=pk, user=request.user)
            for field in ['name', 'icon', 'color']:
                if field in request.data:
                    setattr(cat, field, request.data[field])
            cat.save()
            return Response(CategorySerializer(cat).data)
        except Category.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        Category.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


# Category Rule Views
class CategoryRuleListView(views.APIView):
    def get(self, request):
        rules = CategoryRule.objects.filter(user=request.user)
        return Response({'rules': CategoryRuleSerializer(rules, many=True).data})
    
    def post(self, request):
        rule = CategoryRule.objects.create(
            user=request.user,
            match_type=request.data['match_type'],
            pattern=request.data['pattern'],
            category_id=request.data['category_id']
        )
        return Response(CategoryRuleSerializer(rule).data, status=201)


class CategoryRuleDetailView(views.APIView):
    def patch(self, request, pk):
        try:
            rule = CategoryRule.objects.get(pk=pk, user=request.user)
            for field in ['match_type', 'pattern', 'category_id', 'is_active']:
                if field in request.data:
                    setattr(rule, field, request.data[field])
            rule.save()
            return Response(CategoryRuleSerializer(rule).data)
        except CategoryRule.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        CategoryRule.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


# Budget Views
class BudgetListView(views.APIView):
    def get(self, request):
        from django.db.models import Subquery, OuterRef, DecimalField, Value
        from django.db.models.functions import Coalesce
        
        # Get current month date range
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        
        # Calculate spent amount for each budget's category
        spent_subquery = Transaction.objects.filter(
            user=request.user,
            category_id=OuterRef('category_id'),
            type='debit',
            date__gte=start_of_month,
            date__lte=today
        ).values('category_id').annotate(
            total=Sum('amount')
        ).values('total')
        
        budgets = Budget.objects.filter(user=request.user).select_related('category').annotate(
            spent=Coalesce(Subquery(spent_subquery), Value(0), output_field=DecimalField()),
        )
        
        # Manually calculate remaining, percentage, status for each budget
        budget_data = []
        for budget in budgets:
            spent = float(budget.spent or 0)
            amount = float(budget.amount or 1)
            remaining = amount - spent
            percentage = (spent / amount * 100) if amount > 0 else 0
            
            if percentage >= 100:
                status = 'over'
            elif percentage >= 90:
                status = 'critical'
            elif percentage >= 70:
                status = 'warning'
            else:
                status = 'on_track'
            
            budget_data.append({
                'id': str(budget.id),
                'category_id': str(budget.category_id) if budget.category_id else None,
                'category_name': budget.category.name if budget.category else None,
                'category_icon': budget.category.icon if budget.category else None,
                'category_color': budget.category.color if budget.category else None,
                'amount': float(budget.amount),
                'period': budget.period,
                'spent': spent,
                'remaining': remaining,
                'percentage': round(percentage, 1),
                'status': status,
                'rollover': budget.rollover,
            })
        
        return Response({'budgets': budget_data})
    
    def post(self, request):
        budget = Budget.objects.create(
            user=request.user,
            category_id=request.data['category_id'],
            amount=request.data['amount'],
            period=request.data['period'],
            rollover=request.data.get('rollover', False)
        )
        return Response(BudgetSerializer(budget).data, status=201)


class BudgetDetailView(views.APIView):
    def get(self, request, pk):
        try:
            budget = Budget.objects.get(pk=pk, user=request.user)
            return Response(BudgetSerializer(budget).data)
        except Budget.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def patch(self, request, pk):
        try:
            budget = Budget.objects.get(pk=pk, user=request.user)
            for field in ['amount', 'period', 'rollover']:
                if field in request.data:
                    setattr(budget, field, request.data[field])
            budget.save()
            return Response(BudgetSerializer(budget).data)
        except Budget.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        Budget.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


class BudgetProgressView(views.APIView):
    def get(self, request, pk):
        try:
            budget = Budget.objects.get(pk=pk, user=request.user)
            today = datetime.now().date()
            start = today.replace(day=1)
            spent = Transaction.objects.filter(
                user=request.user, category=budget.category,
                type='debit', date__gte=start
            ).aggregate(total=Sum('amount'))['total'] or 0
            return Response({
                'spent': float(spent),
                'remaining': float(budget.amount - spent),
                'daily_average': float(spent / max(today.day, 1)),
                'projected_total': float(spent / max(today.day, 1) * 30),
                'days_remaining': 30 - today.day
            })
        except Budget.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


# Goal Views
class GoalListView(views.APIView):
    def get(self, request):
        goals = Goal.objects.filter(user=request.user)
        return Response({'goals': GoalSerializer(goals, many=True).data})
    
    def post(self, request):
        goal = Goal.objects.create(
            user=request.user,
            name=request.data['name'],
            emoji=request.data['emoji'],
            target_amount=request.data['target_amount'],
            target_date=request.data.get('target_date')
        )
        return Response(GoalSerializer(goal).data, status=201)


class GoalDetailView(views.APIView):
    def get(self, request, pk):
        try:
            goal = Goal.objects.get(pk=pk, user=request.user)
            return Response(GoalSerializer(goal).data)
        except Goal.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def patch(self, request, pk):
        try:
            goal = Goal.objects.get(pk=pk, user=request.user)
            for field in ['name', 'emoji', 'target_amount', 'target_date']:
                if field in request.data:
                    setattr(goal, field, request.data[field])
            goal.save()
            return Response(GoalSerializer(goal).data)
        except Goal.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        Goal.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


class GoalContributeView(views.APIView):
    def post(self, request, pk):
        try:
            goal = Goal.objects.get(pk=pk, user=request.user)
            amount = Decimal(str(request.data['amount']))
            GoalContribution.objects.create(goal=goal, amount=amount, date=datetime.now().date())
            goal.current_amount += amount
            if goal.current_amount >= goal.target_amount:
                goal.status = 'completed'
            goal.save()
            return Response(GoalSerializer(goal).data)
        except Goal.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


# Recurring Views
class RecurringListView(views.APIView):
    def get(self, request):
        recurring = RecurringTransaction.objects.filter(user=request.user)
        return Response({'recurring': RecurringSerializer(recurring, many=True).data})
    
    def post(self, request):
        # Handle empty strings as None for optional fields
        category_id = request.data.get('category_id')
        account_id = request.data.get('account_id')
        if category_id == '' or category_id == 'undefined':
            category_id = None
        if account_id == '' or account_id == 'undefined':
            account_id = None
            
        rec = RecurringTransaction.objects.create(
            user=request.user,
            name=request.data['name'],
            icon=request.data.get('icon', '📦'),
            amount=request.data['amount'],
            frequency=request.data['frequency'],
            next_date=request.data.get('start_date') or request.data.get('next_date'),
            category_id=category_id,
            account_id=account_id,
            reminder_days=request.data.get('reminder_days'),
            type=request.data.get('type', 'bill')
        )
        return Response(RecurringSerializer(rec).data, status=201)


class RecurringDetailView(views.APIView):
    def patch(self, request, pk):
        try:
            rec = RecurringTransaction.objects.get(pk=pk, user=request.user)
            for field in ['name', 'amount', 'frequency', 'status', 'reminder_days', 'type']:
                if field in request.data:
                    setattr(rec, field, request.data[field])
            rec.save()
            return Response(RecurringSerializer(rec).data)
        except RecurringTransaction.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        RecurringTransaction.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


class RecurringUpcomingView(views.APIView):
    def get(self, request):
        upcoming = RecurringTransaction.objects.filter(
            user=request.user, status='active',
            next_date__lte=datetime.now().date() + timedelta(days=30)
        ).order_by('next_date')
        total = upcoming.aggregate(total=Sum('amount'))['total'] or 0
        return Response({
            'upcoming': RecurringSerializer(upcoming, many=True).data,
            'total_due_30_days': float(total)
        })


# Report Views
class MonthlyReportView(views.APIView):
    def get(self, request):
        year = int(request.query_params.get('year', datetime.now().year))
        month = int(request.query_params.get('month', datetime.now().month))
        
        txns = Transaction.objects.filter(user=request.user, date__year=year, date__month=month)
        income = txns.filter(type='credit').aggregate(total=Sum('amount'))['total'] or 0
        expenses = txns.filter(type='debit').aggregate(total=Sum('amount'))['total'] or 0
        
        spending_by_cat = txns.filter(type='debit').values('category__name', 'category__color').annotate(
            amount=Sum('amount')
        )
        
        # Helper to format category spending
        spending_formatted = []
        for item in spending_by_cat:
            spending_formatted.append({
                'category_name': item['category__name'],
                'category_color': item['category__color'],
                'amount': float(item['amount']),
                'percentage': float(item['amount'] / expenses * 100) if expenses > 0 else 0
            })

        return Response({
            'summary': {
                'total_income': float(income),
                'total_expenses': float(expenses),
                'net': float(income - expenses),
                'savings_rate': float((income - expenses) / income * 100) if income else 0
            },
            'spending_by_category': spending_formatted,
            'income_by_source': [],
            'top_merchants': [],
            'budget_performance': [],
            'comparison': {'income_change_percent': 0, 'expense_change_percent': 0}
        })


class NetWorthView(views.APIView):
    def get(self, request):
        accounts = Account.objects.filter(user=request.user)
        current_net_worth = accounts.aggregate(total=Sum('balance'))['total'] or 0
        current_net_worth = float(current_net_worth)
        
        # Calculate history for last 30 days
        today = datetime.now().date()
        data_points = []
        
        # We start from current balance and work backwards
        running_balance = current_net_worth
        
        # Add today's point
        data_points.append({
            'date': today.isoformat(),
            'net_worth': running_balance
        })
        
        # Work backwards for 29 days
        for i in range(1, 30):
            day = today - timedelta(days=i)
            # Find transactions for this specific day
            day_txns = Transaction.objects.filter(
                user=request.user,
                date=day
            )
            
            # Reverse the effect of transactions:
            # - If we had income (credit), balance was LOWER before
            # - If we had expense (debit), balance was HIGHER before
            day_income = day_txns.filter(type='credit').aggregate(total=Sum('amount'))['total'] or 0
            day_expense = day_txns.filter(type='debit').aggregate(total=Sum('amount'))['total'] or 0
            
            # Previous Balance = Current Balance - Income + Expense
            running_balance = running_balance - float(day_income) + float(day_expense)
            
            data_points.append({
                'date': day.isoformat(),
                'net_worth': running_balance
            })
            
        # Reverse to get chronological order
        data_points.reverse()
        
        # Calculate percent change (30 days ago vs now)
        start_balance = data_points[0]['net_worth']
        if start_balance != 0:
            change_percent = ((current_net_worth - start_balance) / start_balance) * 100
        else:
            change_percent = 100 if current_net_worth > 0 else 0
            
        return Response({
            'data_points': data_points,
            'current_net_worth': current_net_worth,
            'change_percent': round(change_percent, 1)
        })


class SpendingTrendsView(views.APIView):
    def get(self, request):
        return Response({'trends': []})


class CashFlowView(views.APIView):
    """Cash flow data for the last 6 months showing income vs expenses"""
    def get(self, request):
        from dateutil.relativedelta import relativedelta
        
        period = request.query_params.get('period', 'monthly')
        today = datetime.now().date()
        cash_flow_data = []
        
        if period == 'yearly':
            # Last 5 years
            for i in range(4, -1, -1):
                year = today.year - i
                start_date = datetime(year, 1, 1).date()
                end_date = datetime(year, 12, 31).date()
                
                txns = Transaction.objects.filter(
                    user=request.user,
                    date__gte=start_date,
                    date__lte=end_date
                )
                
                income = txns.filter(type='credit').aggregate(total=Sum('amount'))['total'] or 0
                expenses = txns.filter(type='debit').aggregate(total=Sum('amount'))['total'] or 0
                
                cash_flow_data.append({
                    'month': str(year),
                    'income': float(income),
                    'expenses': float(expenses),
                })
        else:
            # Last 6 months (default)
            for i in range(5, -1, -1):  # 5, 4, 3, 2, 1, 0 (oldest to newest)
                month_date = today - relativedelta(months=i)
                month_start = month_date.replace(day=1)
                
                # Get end of month
                if month_date.month == 12:
                    month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
                
                # Query transactions for this month
                txns = Transaction.objects.filter(
                    user=request.user,
                    date__gte=month_start,
                    date__lte=month_end
                )
                
                income = txns.filter(type='credit').aggregate(total=Sum('amount'))['total'] or 0
                expenses = txns.filter(type='debit').aggregate(total=Sum('amount'))['total'] or 0
                
                cash_flow_data.append({
                    'month': month_date.strftime('%b'),
                    'income': float(income),
                    'expenses': float(expenses),
                })
        
        return Response({'cash_flow': cash_flow_data})


# Insight Views
class InsightListView(views.APIView):
    def get(self, request):
        insights = Insight.objects.filter(user=request.user, dismissed=False)
        return Response({'insights': InsightSerializer(insights, many=True).data})


class InsightDismissView(views.APIView):
    def post(self, request, pk):
        Insight.objects.filter(pk=pk, user=request.user).update(dismissed=True)
        return Response({'success': True})


# Export Views
class ExportListView(views.APIView):
    def get(self, request):
        exports = Export.objects.filter(user=request.user).order_by('-created_at')
        return Response({'exports': ExportSerializer(exports, many=True).data})
    
    def post(self, request):
        export = Export.objects.create(
            user=request.user,
            type=request.data['type'],
            status='processing'
        )
        return Response({'job_id': str(export.id), 'status': 'processing'}, status=201)


class ExportDetailView(views.APIView):
    def get(self, request, pk):
        try:
            export = Export.objects.get(pk=pk, user=request.user)
            return Response(ExportSerializer(export).data)
        except Export.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


# Connection Views
class ConnectionListView(views.APIView):
    def get(self, request):
        conns = Connection.objects.filter(user=request.user)
        return Response({'connections': ConnectionSerializer(conns, many=True).data})


class ConnectionDetailView(views.APIView):
    def get(self, request, pk):
        try:
            conn = Connection.objects.get(pk=pk, user=request.user)
            return Response(ConnectionSerializer(conn).data)
        except Connection.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
    
    def delete(self, request, pk):
        Connection.objects.filter(pk=pk, user=request.user).delete()
        return Response({'success': True})


class ConnectionSyncView(views.APIView):
    def post(self, request, pk):
        return Response({'job_id': 'sync-job', 'status': 'processing'})
