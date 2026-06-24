from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Unit, UnitAmenity
from .forms import UnitForm, UnitAmenityForm
from accounts.models import require_landlord_sub

@login_required
def unit_list(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    units = Unit.objects.filter(property__owner=request.user).select_related('property')
    return render(request, 'units/list.html', {'units': units, 'active_tab': 'units'})

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
    units = Unit.objects.filter(property__owner=request.user, status='vacant').select_related('property')
    return render(request, 'units/vacancies.html', {'units': units, 'active_tab': 'vacancies'})
