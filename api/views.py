from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from .serializers import (
    UserSerializer, ProfileSerializer, HouseTypeSerializer,
    PropertySerializer, PropertyCreateUpdateSerializer, UnitSerializer,
    UnitCreateUpdateSerializer, TenantDetailSerializer,
    LandlordDashboardSerializer, SubscriptionPlanSerializer,
    LandlordSubscriptionSerializer, LandlordDetailSerializer,
    TenancySerializer, RentPaymentSerializer, MpesaTransactionSerializer,
    LeaseAgreementSerializer, MaintenanceRequestSerializer,
    UtilityBillSerializer, AdminListingSerializer, InquirySerializer,
)
from .permissions import IsAdmin, IsTenant, IsLandlord
from accounts.models import (
    Profile, PlatformConfig, SubscriptionPlan, LandlordSubscription,
    landlord_has_active_sub, landlord_trial_info, landlord_subscription_status,
)
from properties.models import Property
from units.models import Unit, UnitAmenity
from core.models import HouseType
from tenants.models import (
    Tenancy, RentPayment, MpesaTransaction, LeaseAgreement,
    MaintenanceRequest, UtilityBill,
)
from tenants.mpesa_utils import stk_push
from tenants.rent_utils import generate_rent_payments
from website.models import AdminListing, Inquiry


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not hasattr(user, 'profile'):
            return Response({'error': 'No profile found'}, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': ProfileSerializer(user.profile).data,
        })


class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile


class HouseTypeListView(generics.ListAPIView):
    queryset = HouseType.objects.all()
    serializer_class = HouseTypeSerializer
    permission_classes = [permissions.AllowAny]


class TenantDashboardView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        user = request.user
        tenancy = Tenancy.objects.filter(tenant=user, status='active').first()
        if not tenancy:
            return Response({
                'tenancy': None,
                'balance': 0,
                'pending_payments': [],
                'recent_payments': [],
                'recent_maintenance': [],
            })
        balance = RentPayment.objects.filter(
            tenancy=tenancy, status__in=['pending', 'overdue']
        ).aggregate(total=Sum('amount'))['total'] or 0
        pending = RentPayment.objects.filter(
            tenancy=tenancy, status__in=['pending', 'overdue']
        ).order_by('due_date')[:5]
        recent_payments = RentPayment.objects.filter(
            tenancy=tenancy, status='paid'
        ).order_by('-paid_date')[:5]
        recent_maintenance = MaintenanceRequest.objects.filter(
            tenant=user
        ).order_by('-created_at')[:3]
        return Response({
            'tenancy': TenancySerializer(tenancy).data,
            'balance': balance,
            'pending_payments': RentPaymentSerializer(pending, many=True).data,
            'recent_payments': RentPaymentSerializer(recent_payments, many=True).data,
            'recent_maintenance': MaintenanceRequestSerializer(recent_maintenance, many=True).data,
        })


class TenantPaymentsView(generics.ListAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsTenant]

    def get_queryset(self):
        tenancy = Tenancy.objects.filter(tenant=self.request.user, status='active').first()
        if not tenancy:
            return RentPayment.objects.none()
        return RentPayment.objects.filter(tenancy=tenancy).order_by('-due_date')


class TenantMaintenanceListCreateView(generics.ListCreateAPIView):
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsTenant]

    def get_queryset(self):
        return MaintenanceRequest.objects.filter(tenant=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        tenancy = Tenancy.objects.filter(tenant=self.request.user, status='active').first()
        if not tenancy:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('No active tenancy found')
        serializer.save(tenant=self.request.user, unit=tenancy.unit)


class TenantLeaseView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
        if not tenancy:
            return Response({'lease': None})
        lease = LeaseAgreement.objects.filter(tenancy=tenancy).first()
        if not lease:
            return Response({'lease': None})
        return Response({'lease': LeaseAgreementSerializer(lease).data})


class TenantUtilitiesView(generics.ListAPIView):
    serializer_class = UtilityBillSerializer
    permission_classes = [IsTenant]

    def get_queryset(self):
        tenancy = Tenancy.objects.filter(tenant=self.request.user, status='active').first()
        if not tenancy:
            return UtilityBill.objects.none()
        return UtilityBill.objects.filter(tenancy=tenancy).order_by('-created_at')


class TenantPayView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
        if not tenancy:
            return Response({'pending': [], 'balance': 0})
        pending = RentPayment.objects.filter(
            tenancy=tenancy, status__in=['pending', 'overdue']
        ).order_by('due_date')
        balance = pending.aggregate(total=Sum('amount'))['total'] or 0
        return Response({
            'pending': RentPaymentSerializer(pending, many=True).data,
            'balance': balance,
            'phone': request.user.profile.phone,
        })


class AdminDashboardView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        landlords = Profile.objects.filter(role='landlord').count()
        tenants = Profile.objects.filter(role='tenant').count()
        properties = Property.objects.count()
        units = Unit.objects.count()
        active_subs = LandlordSubscription.objects.filter(status='active').count()
        expired_subs = LandlordSubscription.objects.filter(status='expired').count()
        total_revenue = LandlordSubscription.objects.filter(
            status='active'
        ).aggregate(total=Sum('amount'))['total'] or 0
        recent_inquiries = Inquiry.objects.order_by('-created_at')[:5]
        return Response({
            'landlords': landlords,
            'tenants': tenants,
            'properties': properties,
            'units': units,
            'active_subscriptions': active_subs,
            'expired_subscriptions': expired_subs,
            'total_revenue': total_revenue,
            'recent_inquiries': InquirySerializer(recent_inquiries, many=True).data,
        })


class AdminLandlordListView(generics.ListAPIView):
    serializer_class = LandlordDetailSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Profile.objects.filter(role='landlord')
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        return qs


class AdminLandlordDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, landlord_id):
        try:
            profile = Profile.objects.get(user__id=landlord_id, role='landlord')
        except Profile.DoesNotExist:
            return Response({'error': 'Landlord not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(LandlordDetailSerializer(profile).data)


class AdminLandlordCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email', '')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        phone = request.data.get('phone', '')
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        profile = Profile.objects.create(
            user=user, role='landlord', phone=phone,
            trial_started_at=timezone.now(),
        )
        config, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00, 'trial_days': 14})
        profile.fee_per_unit = config.fee_per_unit
        profile.save()
        return Response(ProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class AdminAssignSubscriptionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, landlord_id):
        try:
            user = User.objects.get(id=landlord_id, profile__role='landlord')
        except User.DoesNotExist:
            return Response({'error': 'Landlord not found'}, status=status.HTTP_404_NOT_FOUND)
        plan_id = request.data.get('plan_id')
        unit_count = int(request.data.get('unit_count', 0))
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        fee_per_unit = user.profile.fee_per_unit or 50.00
        amount = unit_count * float(fee_per_unit) * (plan.duration_days / 30)
        today = date.today()
        sub = LandlordSubscription.objects.create(
            landlord=user, plan=plan, unit_count=unit_count,
            amount=amount, start_date=today,
            end_date=today + timedelta(days=plan.duration_days),
            status='active',
        )
        return Response(LandlordSubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


class AdminSetLandlordFeeView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, landlord_id):
        try:
            profile = Profile.objects.get(user__id=landlord_id, role='landlord')
        except Profile.DoesNotExist:
            return Response({'error': 'Landlord not found'}, status=status.HTTP_404_NOT_FOUND)
        fee = request.data.get('fee_per_unit')
        if fee is None:
            return Response({'error': 'fee_per_unit required'}, status=status.HTTP_400_BAD_REQUEST)
        profile.fee_per_unit = fee
        profile.save()
        return Response({'message': 'Fee updated', 'fee_per_unit': str(profile.fee_per_unit)})


class AdminSetLandlordMpesaView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, landlord_id):
        try:
            profile = Profile.objects.get(user__id=landlord_id, role='landlord')
        except Profile.DoesNotExist:
            return Response({'error': 'Landlord not found'}, status=status.HTTP_404_NOT_FOUND)
        fields = [
            'mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_passkey',
            'mpesa_shortcode', 'c2b_shortcode', 'mpesa_callback_url',
            'c2b_confirmation_url', 'c2b_validation_url',
            'b2c_initiator_name', 'b2c_initiator_password', 'b2c_shortcode',
            'b2c_callback_base_url',
        ]
        for field in fields:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        return Response({'message': 'M-Pesa credentials updated'})


class AdminSubscriptionPlansView(generics.ListCreateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdmin]


class AdminPlanToggleView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            plan = SubscriptionPlan.objects.get(pk=pk)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        plan.is_active = not plan.is_active
        plan.save()
        return Response({'is_active': plan.is_active})


class AdminRevenueView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.query_params.get('status', '')
        qs = LandlordSubscription.objects.all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        total = qs.aggregate(total=Sum('amount'))['total'] or 0
        active = qs.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
        return Response({
            'total_revenue': total,
            'active_revenue': active,
            'subscriptions': LandlordSubscriptionSerializer(qs[:50], many=True).data,
        })


class AdminUpdateFeeView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request):
        fee = request.data.get('fee_per_unit')
        if fee is None:
            return Response({'error': 'fee_per_unit required'}, status=status.HTTP_400_BAD_REQUEST)
        config, _ = PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00, 'trial_days': 14})
        config.fee_per_unit = fee
        config.save()
        return Response({'message': 'Global fee updated', 'fee_per_unit': str(config.fee_per_unit)})


class AdminListingsView(generics.ListCreateAPIView):
    serializer_class = AdminListingSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = AdminListing.objects.all()
        search = self.request.query_params.get('search', '')
        status_filter = self.request.query_params.get('status', '')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(county__icontains=search) |
                Q(town__icontains=search)
            )
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AdminListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdminListing.objects.all()
    serializer_class = AdminListingSerializer
    permission_classes = [IsAdmin]


class AdminInquiriesView(generics.ListAPIView):
    serializer_class = InquirySerializer
    permission_classes = [IsAdmin]
    queryset = Inquiry.objects.all().order_by('-created_at')


# ==================== M-PESA STK PUSH (TENANT) ====================

class TenantStkPushView(APIView):
    permission_classes = [IsTenant]

    def post(self, request):
        from decimal import Decimal, InvalidOperation
        amount_raw = request.data.get('amount', '0')
        try:
            amount = Decimal(str(amount_raw))
        except InvalidOperation:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= 0:
            return Response({'error': 'Amount must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        tenancy = Tenancy.objects.filter(tenant=request.user, status='active').first()
        if not tenancy:
            return Response({'error': 'No active tenancy'}, status=status.HTTP_400_BAD_REQUEST)

        phone = request.data.get('phone') or request.user.profile.phone
        if not phone:
            return Response({'error': 'No phone number. Update your profile first.'}, status=status.HTTP_400_BAD_REQUEST)

        landlord = tenancy.unit.property.owner

        payment = RentPayment.objects.create(
            tenancy=tenancy, amount=amount, due_date=timezone.now().date(),
            status='pending', notes='stk_intermediary',
        )

        tx, error = stk_push(payment, phone, landlord)
        if error:
            payment.delete()
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': True,
            'message': 'STK push sent. Enter your M-Pesa PIN.',
            'payment_id': payment.id,
            'checkout_id': tx.checkout_request_id,
        })


class TenantStkStatusView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({'error': 'payment_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pmt = RentPayment.objects.get(pk=payment_id, tenancy__tenant=request.user)
        except RentPayment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        tx = MpesaTransaction.objects.filter(payment=pmt).order_by('-created_at').first()
        return Response({
            'payment_id': pmt.id,
            'payment_status': pmt.status,
            'mpesa_status': tx.status if tx else None,
            'receipt': pmt.reference,
            'amount': str(pmt.amount),
        })


# ==================== LANDLORD API ====================

class LandlordDashboardView(APIView):
    permission_classes = [IsLandlord]

    def get(self, request):
        user = request.user
        from decimal import Decimal
        properties = Property.objects.filter(owner=user)
        units = Unit.objects.filter(property__owner=user)
        properties_count = properties.count()
        units_count = units.count()
        vacant = units.filter(status='vacant').count()
        occupied = units.filter(status='occupied').count()

        tenancies = Tenancy.objects.filter(unit__property__owner=user, status='active')
        tenants_count = tenancies.values('tenant').distinct().count()

        outstanding = RentPayment.objects.filter(
            tenancy__unit__property__owner=user
        ).exclude(status='paid').exclude(notes='stk_intermediary') \
            .aggregate(total=Sum('amount'))['total'] or 0

        first_day = timezone.now().replace(day=1)
        monthly_collected = RentPayment.objects.filter(
            tenancy__unit__property__owner=user, status='paid', paid_date__gte=first_day
        ).aggregate(total=Sum('amount'))['total'] or 0

        pending_maintenance = MaintenanceRequest.objects.filter(
            unit__property__owner=user, status__in=['submitted', 'in_progress']
        ).count()

        sub_status, sub = landlord_subscription_status(user)

        return Response(LandlordDashboardSerializer({
            'properties': properties_count,
            'units': units_count,
            'vacant_units': vacant,
            'occupied_units': occupied,
            'active_tenancies': tenancies.count(),
            'tenants': tenants_count,
            'outstanding_rent': outstanding,
            'monthly_collected': monthly_collected,
            'pending_maintenance': pending_maintenance,
            'subscription_status': sub_status,
            'trial_info': landlord_trial_info(user),
        }).data)


class LandlordPropertyListCreateView(generics.ListCreateAPIView):
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LandlordPropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertyCreateUpdateSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)


class LandlordUnitListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitCreateUpdateSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        queryset = Unit.objects.filter(property__owner=self.request.user)
        prop = self.request.query_params.get('property')
        if prop:
            queryset = queryset.filter(property_id=prop)
        return queryset

    def perform_create(self, serializer):
        prop = serializer.validated_data.get('property')
        if prop.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not own this property')
        unit = serializer.save()
        UnitAmenity.objects.get_or_create(unit=unit)


class LandlordUnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UnitCreateUpdateSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        return Unit.objects.filter(property__owner=self.request.user)


class LandlordTenantListView(generics.ListAPIView):
    serializer_class = TenantDetailSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        qs = Tenancy.objects.filter(unit__property__owner=self.request.user)
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(tenant__username__icontains=search) |
                Q(tenant__first_name__icontains=search) |
                Q(tenant__last_name__icontains=search) |
                Q(unit__unit_number__icontains=search)
            )
        tenant_ids = qs.values_list('tenant_id', flat=True).distinct()
        return Profile.objects.filter(user_id__in=tenant_ids)


class LandlordTenancyListView(generics.ListAPIView):
    serializer_class = TenancySerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        qs = Tenancy.objects.filter(unit__property__owner=self.request.user)\
            .select_related('tenant', 'unit__property')
        status_f = self.request.query_params.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        prop_f = self.request.query_params.get('property')
        if prop_f:
            qs = qs.filter(unit__property_id=prop_f)
        return qs


class LandlordTenancyDetailView(generics.RetrieveAPIView):
    serializer_class = TenancySerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        return Tenancy.objects.filter(unit__property__owner=self.request.user)\
            .select_related('tenant', 'unit__property')


class LandlordRentPaymentsView(generics.ListAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        qs = RentPayment.objects.filter(tenancy__unit__property__owner=self.request.user)
        status_f = self.request.query_params.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        return qs.order_by('-due_date')


class LandlordUtilitiesView(generics.ListAPIView):
    serializer_class = UtilityBillSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        qs = UtilityBill.objects.filter(tenancy__unit__property__owner=self.request.user)
        status_f = self.request.query_params.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        return qs.order_by('-created_at')


class LandlordMaintenanceListView(generics.ListAPIView):
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        qs = MaintenanceRequest.objects.filter(unit__property__owner=self.request.user)
        status_f = self.request.query_params.get('status')
        if status_f:
            qs = qs.filter(status=status_f)
        return qs.order_by('-created_at')


class LandlordMaintenanceUpdateView(APIView):
    permission_classes = [IsLandlord]

    def patch(self, request, pk):
        try:
            m = MaintenanceRequest.objects.get(pk=pk, unit__property__owner=request.user)
        except MaintenanceRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        status_f = request.data.get('status')
        notes = request.data.get('landlord_notes')
        if status_f:
            if status_f not in dict(MaintenanceRequest.STATUS_CHOICES):
                return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
            m.status = status_f
            if status_f == 'resolved':
                m.resolved_at = timezone.now()
        if notes:
            m.landlord_notes = notes
        m.save()
        return Response(MaintenanceRequestSerializer(m).data)


class LandlordProfileUpdateView(APIView):
    permission_classes = [IsLandlord]

    def patch(self, request):
        profile = request.user.profile
        fields = [
            'phone', 'id_number', 'mpesa_consumer_key', 'mpesa_consumer_secret',
            'mpesa_passkey', 'mpesa_shortcode', 'c2b_shortcode',
            'mpesa_callback_url', 'c2b_confirmation_url', 'c2b_validation_url',
            'b2c_initiator_name', 'b2c_initiator_password', 'b2c_shortcode',
            'b2c_callback_base_url',
        ]
        for field in fields:
            if field in request.data:
                setattr(profile, field, request.data[field])
        profile.save()
        return Response({'message': 'Profile updated'})


class LandlordCreateTenancyView(APIView):
    permission_classes = [IsLandlord]

    def post(self, request):
        unit_id = request.data.get('unit')
        tenant_id = request.data.get('tenant')
        start_date = request.data.get('start_date')
        deposit = request.data.get('deposit', 0)
        if not unit_id or not tenant_id or not start_date:
            return Response({'error': 'unit, tenant, and start_date required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            unit = Unit.objects.get(pk=unit_id, property__owner=request.user)
        except Unit.DoesNotExist:
            return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            tenant = User.objects.get(pk=tenant_id, profile__role='tenant')
        except User.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        if unit.status == 'occupied':
            return Response({'error': 'Unit is already occupied'}, status=status.HTTP_400_BAD_REQUEST)
        from datetime import datetime as dt
        try:
            start = dt.strptime(str(start_date), '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid start_date format (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)
        tenancy = Tenancy.objects.create(
            tenant=tenant, unit=unit, start_date=start,
            monthly_rent=unit.monthly_rent, deposit_paid=deposit,
        )
        unit.status = 'occupied'
        unit.save()
        generate_rent_payments(landlord=request.user)
        return Response(TenancySerializer(tenancy).data, status=status.HTTP_201_CREATED)


class LandlordEndTenancyView(APIView):
    permission_classes = [IsLandlord]

    def post(self, request, pk):
        try:
            tenancy = Tenancy.objects.get(pk=pk, unit__property__owner=request.user, status='active')
        except Tenancy.DoesNotExist:
            return Response({'error': 'Active tenancy not found'}, status=status.HTTP_404_NOT_FOUND)
        tenancy.status = 'ended'
        tenancy.end_date = timezone.now().date()
        tenancy.save()
        tenancy.unit.status = 'vacant'
        tenancy.unit.save()
        return Response({'message': 'Tenancy ended', 'tenancy': TenancySerializer(tenancy).data})


class LandlordInitiateStkPushView(APIView):
    permission_classes = [IsLandlord]

    def post(self, request, payment_id):
        try:
            payment = RentPayment.objects.get(pk=payment_id, tenancy__unit__property__owner=request.user)
        except RentPayment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        phone = request.data.get('phone') or payment.tenancy.tenant.profile.phone
        if not phone:
            return Response({'error': 'No phone number for tenant'}, status=status.HTTP_400_BAD_REQUEST)
        tx, error = stk_push(payment, phone, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'success': True,
            'message': 'STK push sent',
            'payment_id': payment.id,
            'checkout_id': tx.checkout_request_id,
        })
