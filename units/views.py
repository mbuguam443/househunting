from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from .models import Unit, UnitAmenity
from properties.models import Property
from .forms import UnitForm, UnitAmenityForm
from accounts.models import require_landlord_sub
from core.pagination import paginate
from tenants.models import Tenancy

@login_required
def unit_list(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    active_tenancies = Tenancy.objects.filter(status='active').select_related('tenant')
    qs = Unit.objects.filter(property__owner=request.user).select_related('property').prefetch_related(
        Prefetch('tenancies', queryset=active_tenancies, to_attr='active_tenancies')
    )
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(unit_number__icontains=q) | qs.filter(property__name__icontains=q) | qs.filter(house_type__icontains=q)
    status_f = request.GET.get('status', '').strip()
    if status_f:
        qs = qs.filter(status=status_f)
    prop_f = request.GET.get('property', '').strip()
    if prop_f:
        qs = qs.filter(property_id=prop_f)
    properties = Property.objects.filter(owner=request.user)
    page_obj = paginate(request, qs)
    return render(request, 'units/list.html', {'units': page_obj, 'q': q, 'status_f': status_f, 'prop_f': prop_f, 'properties': properties, 'active_tab': 'units'})

@login_required
def unit_create(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    if request.method == 'POST':
        form = UnitForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            unit = form.save()
            UnitAmenity.objects.get_or_create(unit=unit)
            action = 'published' if unit.status == 'vacant' else 'saved'
            messages.success(request, f'Unit {unit.unit_number} created and {action}.')
            return redirect('units:list')
    else:
        form = UnitForm(user=request.user)
    return render(request, 'units/form.html', {'form': form, 'title': 'Add Unit', 'active_tab': 'units'})

@login_required
def unit_update(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    unit = get_object_or_404(Unit, pk=pk, property__owner=request.user)
    amenity, _ = UnitAmenity.objects.get_or_create(unit=unit)
    if request.method == 'POST':
        form = UnitForm(request.POST, request.FILES, instance=unit, user=request.user)
        amenity_form = UnitAmenityForm(request.POST, instance=amenity)
        if form.is_valid() and amenity_form.is_valid():
            form.save()
            amenity_form.save()
            action = 'published to the website' if unit.status == 'vacant' else 'removed from public listings'
            messages.success(request, f'Unit {unit.unit_number} updated and {action}.')
            return redirect('units:list')
    else:
        form = UnitForm(instance=unit, user=request.user)
        amenity_form = UnitAmenityForm(instance=amenity)
    return render(request, 'units/form.html', {
        'form': form, 'amenity_form': amenity_form, 'title': 'Edit Unit', 'unit': unit, 'active_tab': 'units'
    })

@login_required
def unit_delete(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    unit = get_object_or_404(Unit, pk=pk, property__owner=request.user)
    unit.delete()
    messages.success(request, 'Unit deleted.')
    return redirect('units:list')

@login_required
def vacancies(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    qs = Unit.objects.filter(property__owner=request.user, status='vacant').select_related('property')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(unit_number__icontains=q) | qs.filter(property__name__icontains=q) | qs.filter(house_type__icontains=q)
    prop_f = request.GET.get('property', '').strip()
    if prop_f:
        qs = qs.filter(property_id=prop_f)
    type_f = request.GET.get('type', '').strip()
    if type_f:
        qs = qs.filter(house_type=type_f)
    properties = Property.objects.filter(owner=request.user)
    page_obj = paginate(request, qs)
    return render(request, 'units/vacancies.html', {'units': page_obj, 'q': q, 'prop_f': prop_f, 'type_f': type_f, 'properties': properties, 'active_tab': 'vacancies'})
