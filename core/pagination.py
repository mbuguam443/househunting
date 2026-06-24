from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate(request, queryset, per_page=15):
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj