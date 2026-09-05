from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Profile, PlatformConfig, SubscriptionPlan, LandlordSubscription
from properties.models import Property
from units.models import Unit, UnitAmenity
from core.models import HouseType
from tenants.models import (
    Tenancy, RentPayment, MpesaTransaction, LeaseAgreement,
    MaintenanceRequest, UtilityBill, C2BTransaction, B2CTransaction,
)
from website.models import AdminListing, AdminListingImage, Inquiry


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'role_display', 'phone', 'id_number', 'avatar',
            'fee_per_unit', 'trial_started_at', 'created_at',
        ]


class HouseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseType
        fields = ['id', 'name', 'slug']


class PropertySerializer(serializers.ModelSerializer):
    total_units = serializers.SerializerMethodField()
    vacant_units = serializers.SerializerMethodField()
    occupied_units = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'name', 'description', 'county', 'town', 'estate', 'address',
            'latitude', 'longitude', 'image', 'water_rate', 'electricity_rate',
            'trash_rate', 'total_units', 'vacant_units', 'occupied_units',
            'created_at', 'updated_at',
        ]

    def get_total_units(self, obj):
        return obj.total_units()

    def get_vacant_units(self, obj):
        return obj.vacant_units()

    def get_occupied_units(self, obj):
        return obj.occupied_units()


class UnitAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAmenity
        fields = ['water', 'electricity', 'parking', 'security', 'internet', 'furnished']


class UnitSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    house_type_name = serializers.CharField(source='house_type.name', read_only=True)
    amenities = UnitAmenitySerializer(read_only=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'property', 'property_name', 'unit_number', 'house_type',
            'house_type_name', 'bedrooms', 'bathrooms', 'monthly_rent', 'deposit',
            'floor', 'description', 'status', 'available_from',
            'image', 'image_2', 'image_3', 'amenities',
            'created_at', 'updated_at',
        ]


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'amount', 'duration_days', 'description', 'is_active', 'created_at']


class LandlordSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    landlord_username = serializers.CharField(source='landlord.username', read_only=True)

    class Meta:
        model = LandlordSubscription
        fields = [
            'id', 'landlord', 'landlord_username', 'plan', 'plan_name',
            'unit_count', 'amount', 'start_date', 'end_date', 'status',
            'payment_reference', 'notes', 'created_at',
        ]


class TenancySerializer(serializers.ModelSerializer):
    unit_number = serializers.CharField(source='unit.unit_number', read_only=True)
    property_name = serializers.CharField(source='unit.property.name', read_only=True)
    tenant_name = serializers.SerializerMethodField()

    class Meta:
        model = Tenancy
        fields = [
            'id', 'tenant', 'tenant_name', 'unit', 'unit_number', 'property_name',
            'start_date', 'end_date', 'deposit_paid', 'monthly_rent', 'status',
            'created_at', 'updated_at',
        ]

    def get_tenant_name(self, obj):
        return obj.tenant.get_full_name() or obj.tenant.username


class RentPaymentSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    unit_number = serializers.SerializerMethodField()

    class Meta:
        model = RentPayment
        fields = [
            'id', 'tenancy', 'amount', 'due_date', 'paid_date', 'status',
            'payment_method', 'reference', 'notes', 'tenant_name', 'unit_number',
            'created_at',
        ]

    def get_tenant_name(self, obj):
        return obj.tenancy.tenant.get_full_name() or obj.tenancy.tenant.username

    def get_unit_number(self, obj):
        return obj.tenancy.unit.unit_number


class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = [
            'id', 'payment', 'phone', 'amount', 'merchant_request_id',
            'checkout_request_id', 'response_code', 'response_description',
            'receipt', 'transaction_date', 'result_code', 'result_desc',
            'status', 'created_at',
        ]


class LeaseAgreementSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    unit_number = serializers.SerializerMethodField()

    class Meta:
        model = LeaseAgreement
        fields = [
            'id', 'tenancy', 'start_date', 'end_date', 'monthly_rent',
            'deposit_amount', 'payment_due_day', 'late_fee', 'notice_period_days',
            'terms', 'clauses', 'status', 'landlord_accepted', 'landlord_accepted_at',
            'tenant_accepted', 'tenant_accepted_at', 'tenant_name', 'unit_number',
            'created_at', 'updated_at',
        ]

    def get_tenant_name(self, obj):
        return obj.tenancy.tenant.get_full_name() or obj.tenancy.tenant.username

    def get_unit_number(self, obj):
        return obj.tenancy.unit.unit_number


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    unit_number = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = [
            'id', 'tenant', 'tenant_name', 'unit', 'unit_number', 'title',
            'description', 'priority', 'status', 'landlord_notes',
            'created_at', 'resolved_at',
        ]

    def get_tenant_name(self, obj):
        return obj.tenant.get_full_name() or obj.tenant.username

    def get_unit_number(self, obj):
        return obj.unit.unit_number


class UtilityBillSerializer(serializers.ModelSerializer):
    utility_type_display = serializers.CharField(source='get_utility_type_display', read_only=True)

    class Meta:
        model = UtilityBill
        fields = [
            'id', 'tenancy', 'utility_type', 'utility_type_display', 'amount',
            'period_start', 'period_end', 'due_date', 'units_consumed',
            'rate_per_unit', 'status', 'paid_date', 'payment_method',
            'reference', 'notes', 'created_at',
        ]


class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'owner', 'name', 'description', 'county', 'town', 'estate', 'address',
            'latitude', 'longitude', 'image', 'water_rate', 'electricity_rate',
            'trash_rate', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class UnitCreateUpdateSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    house_type_name = serializers.CharField(source='house_type.name', read_only=True)
    amenities = UnitAmenitySerializer(read_only=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'property', 'property_name', 'unit_number', 'house_type',
            'house_type_name', 'bedrooms', 'bathrooms', 'monthly_rent', 'deposit',
            'floor', 'description', 'status', 'available_from',
            'image', 'image_2', 'image_3', 'amenities',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'property_name', 'house_type_name', 'amenities', 'created_at', 'updated_at']


class TenantDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'phone', 'id_number', 'avatar', 'created_at']


class LandlordDashboardSerializer(serializers.Serializer):
    properties = serializers.IntegerField()
    units = serializers.IntegerField()
    vacant_units = serializers.IntegerField()
    occupied_units = serializers.IntegerField()
    active_tenancies = serializers.IntegerField()
    tenants = serializers.IntegerField()
    outstanding_rent = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_maintenance = serializers.IntegerField()
    subscription_status = serializers.CharField()
    trial_info = serializers.JSONField(read_only=True)


class AdminListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminListingImage
        fields = ['id', 'image', 'order']


class AdminListingSerializer(serializers.ModelSerializer):
    house_type_name = serializers.CharField(source='house_type.name', read_only=True)
    images = AdminListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = AdminListing
        fields = [
            'id', 'title', 'description', 'county', 'town', 'estate',
            'house_type', 'house_type_name', 'bedrooms', 'bathrooms', 'rent',
            'contact_name', 'contact_phone', 'image', 'latitude', 'longitude',
            'status', 'images', 'created_at', 'updated_at',
        ]


class InquirySerializer(serializers.ModelSerializer):
    unit_number = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            'id', 'unit', 'unit_number', 'name', 'email', 'phone',
            'message', 'is_read', 'created_at',
        ]

    def get_unit_number(self, obj):
        return obj.unit.unit_number if obj.unit else None


class LandlordDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    properties_count = serializers.SerializerMethodField()
    units_count = serializers.SerializerMethodField()
    tenants_count = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    trial_info = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'phone', 'id_number', 'fee_per_unit',
            'trial_started_at', 'properties_count', 'units_count',
            'tenants_count', 'subscription_status', 'trial_info', 'created_at',
        ]

    def get_properties_count(self, obj):
        return Property.objects.filter(owner=obj.user).count()

    def get_units_count(self, obj):
        return Unit.objects.filter(property__owner=obj.user).count()

    def get_tenants_count(self, obj):
        from tenants.models import Tenancy
        return Tenancy.objects.filter(unit__property__owner=obj.user, status='active').count()

    def get_subscription_status(self, obj):
        from accounts.models import landlord_subscription_status
        status, sub = landlord_subscription_status(obj.user)
        if sub:
            return {
                'status': status,
                'plan': sub.plan.name if sub.plan else None,
                'end_date': sub.end_date,
                'amount': sub.amount,
            }
        return {'status': status}

    def get_trial_info(self, obj):
        from accounts.models import landlord_trial_info
        return landlord_trial_info(obj.user)
