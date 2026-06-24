from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Property
from .forms import PropertyForm
from accounts.models import require_landlord_sub

@login_required
def property_list(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    properties = request.user.properties.all()
    return render(request, 'properties/list.html', {'properties': properties, 'active_tab': 'properties'})

@login_required
def property_create(request):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.owner = request.user
            prop.save()
            messages.success(request, f'Property "{prop.name}" created.')
            return redirect('properties:list')
    else:
        form = PropertyForm()
    return render(request, 'properties/form.html', {'form': form, 'title': 'Add Property', 'active_tab': 'properties'})

@login_required
def property_update(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated.')
            return redirect('properties:list')
    else:
        form = PropertyForm(instance=prop)
    return render(request, 'properties/form.html', {'form': form, 'title': 'Edit Property', 'prop': prop, 'active_tab': 'properties'})

@login_required
def property_delete(request, pk):
    ok, resp = require_landlord_sub(request.user)
    if not ok:
        return resp
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    prop.delete()
    messages.success(request, 'Property deleted.')
    return redirect('properties:list')
