"""Serializers for NairaTrack API"""
from rest_framework import serializers
from .models import *


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'connection_id', 'name', 'type', 'account_number_masked', 
                  'currency', 'balance', 'available_balance', 'last_synced_at']


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_color = serializers.CharField(source='category.color', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'account_id', 'date', 'description', 'merchant_name', 'amount',
                  'type', 'category_id', 'category_name', 'category_color', 'notes', 
                  'is_recurring', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    transaction_count_this_month = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'is_system', 'parent_id', 'transaction_count_this_month']


class CategoryRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = CategoryRule
        fields = ['id', 'match_type', 'pattern', 'category_id', 'category_name', 'is_active', 'applied_count']


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    spent = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, default=0)
    remaining = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True, default=0)
    percentage = serializers.FloatField(read_only=True, default=0)
    status = serializers.CharField(read_only=True, default='on_track')
    
    class Meta:
        model = Budget
        fields = ['id', 'category_id', 'category_name', 'category_icon', 'category_color',
                  'amount', 'period', 'spent', 'remaining', 'percentage', 'status', 'rollover']


class GoalSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()
    monthly_contribution_needed = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id', 'name', 'emoji', 'target_amount', 'current_amount', 'percentage',
                  'target_date', 'monthly_contribution_needed', 'status']
    
    def get_percentage(self, obj):
        if obj.target_amount:
            return float(obj.current_amount / obj.target_amount * 100)
        return 0
    
    def get_monthly_contribution_needed(self, obj):
        return 0


class RecurringSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = RecurringTransaction
        fields = ['id', 'name', 'icon', 'amount', 'frequency', 'next_date', 'category_id',
                  'category_name', 'account_id', 'status', 'reminder_days', 'type']


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = ['id', 'type', 'title', 'message', 'severity', 'data', 'created_at']


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = ['id', 'type', 'status', 'created_at', 'download_url', 'expires_at', 'file_size', 'error']


class ConnectionSerializer(serializers.ModelSerializer):
    accounts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Connection
        fields = ['id', 'institution_name', 'institution_logo', 'status', 'accounts_count', 'last_synced_at']
    
    def get_accounts_count(self, obj):
        return obj.accounts.count()
