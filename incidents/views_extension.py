
@login_required
def past_incidents_view(request):
    """View for viewing resolved and closed incidents"""
    company = request.company
    
    incidents = Incident.objects.filter(
        company=company,
        status__in=['resolved', 'closed']
    ).order_by('-created_at')
    
    # Filter by search
    search_query = request.GET.get('search')
    if search_query:
        incidents = incidents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(incident_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(incidents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search_query or '',
    }
    return render(request, 'incidents/past_incidents.html', context)


@login_required
def log_explorer_view(request):
    """View for exploring logs and AI analysis"""
    company = request.company
    
    # Get recent logs from company incidents
    recent_logs = IncidentLog.objects.filter(
        incident__company=company
    ).order_by('-uploaded_at')[:20]
    
    context = {
        'recent_logs': recent_logs,
    }
    return render(request, 'incidents/log_explorer.html', context)


@login_required
def ai_suggest_severity(request):
    """HTMX endpoint for suggesting severity"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    title = request.POST.get('title', '')
    description = request.POST.get('description', '')
    
    analyzer = GeminiAnalyzer()
    result = analyzer.suggest_severity(title, description)
    
    return JsonResponse(result)


@login_required
def ai_generate_postmortem(request, incident_id):
    """HTMX endpoint for generating post-mortem"""
    company = request.company
    incident = get_object_or_404(Incident, id=incident_id, company=company)
    
    analyzer = GeminiAnalyzer()
    report = analyzer.generate_postmortem(incident)
    
    return render(request, 'incidents/partials/postmortem.html', {'report': report})


@login_required
def ai_explain_logs(request):
    """HTMX endpoint for explaining logs"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    log_content = request.POST.get('log_content', '')
    if not log_content:
        return JsonResponse({'explanation': 'No content provided'})
        
    analyzer = GeminiAnalyzer()
    explanation = analyzer.explain_logs(log_content)
    
    # Return as HTML for HTMX target
    import markdown
    html_content = markdown.markdown(explanation)
    
    return HttpResponse(html_content)
