"""Core URL routes for NairaTrack API"""
from django.urls import path
from . import views

urlpatterns = [
    # Health Check
    path('health', views.HealthCheckView.as_view()),
    
    # Auth
    path('auth/me', views.UserMeView.as_view()),
    path('auth/profile', views.UserMeView.as_view()),
    
    # Accounts
    path('accounts', views.AccountListView.as_view()),
    path('accounts/<uuid:pk>', views.AccountDetailView.as_view()),
    
    # Transactions
    path('transactions', views.TransactionListView.as_view()),
    path('transactions/<uuid:pk>', views.TransactionDetailView.as_view()),
    path('transactions/bulk-categorize', views.BulkCategorizeView.as_view()),
    path('transactions/manual', views.ManualTransactionView.as_view()),
    
    # Categories
    path('categories', views.CategoryListView.as_view()),
    path('categories/<uuid:pk>', views.CategoryDetailView.as_view()),
    
    # Category Rules
    path('category-rules', views.CategoryRuleListView.as_view()),
    path('category-rules/<uuid:pk>', views.CategoryRuleDetailView.as_view()),
    
    # Budgets
    path('budgets', views.BudgetListView.as_view()),
    path('budgets/<uuid:pk>', views.BudgetDetailView.as_view()),
    path('budgets/<uuid:pk>/progress', views.BudgetProgressView.as_view()),
    
    # Goals
    path('goals', views.GoalListView.as_view()),
    path('goals/<uuid:pk>', views.GoalDetailView.as_view()),
    path('goals/<uuid:pk>/contribute', views.GoalContributeView.as_view()),
    
    # Recurring
    path('recurring', views.RecurringListView.as_view()),
    path('recurring/upcoming', views.RecurringUpcomingView.as_view()),
    path('recurring/<uuid:pk>', views.RecurringDetailView.as_view()),
    
    # Reports
    path('reports/monthly', views.MonthlyReportView.as_view()),
    path('reports/net-worth', views.NetWorthView.as_view()),
    path('reports/spending-trends', views.SpendingTrendsView.as_view()),
    path('reports/cash-flow', views.CashFlowView.as_view()),
    
    # Insights
    path('insights', views.InsightListView.as_view()),
    path('insights/<uuid:pk>/dismiss', views.InsightDismissView.as_view()),
    
    # Exports
    path('exports', views.ExportListView.as_view()),
    path('exports/<uuid:pk>', views.ExportDetailView.as_view()),
    
    # Connections
    path('connections', views.ConnectionListView.as_view()),
    path('connections/<uuid:pk>', views.ConnectionDetailView.as_view()),
    path('connections/<uuid:pk>/sync', views.ConnectionSyncView.as_view()),
]
