# encoding: utf-8

from __future__ import unicode_literals

from django.db import transaction
from django.contrib import messages
from django.forms.models import modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from core.helpers import person_required
from core.utils import initialize_form, initialize_form_set

from ..forms import ProgrammeSelfServiceForm, get_sired_invitation_formset
from ..helpers import programme_event_required
from ..models import Invitation, ProgrammeRole, FreeformOrganizer


@programme_event_required
@person_required
def programme_accept_invitation_view(request, event, code):
    invitation = get_object_or_404(Invitation, programme__category__event=event, code=code)
    programme = invitation.programme

    if invitation.state == 'used' and programme.host_can_edit:
        messages.warning(request, _('You have already accepted this invitation. You can edit the programme below.'))
        return redirect('programme_profile_detail_view', programme.pk)
    elif invitation.state == 'used' and not programme.host_can_edit:
        messages.error(request, _('You have already accepted this invitation. You can no longer edit the programme.'))
        return redirect('programme_profile_view')
    elif not (invitation.state == 'valid' and programme.host_can_edit):
        messages.error(request, _('The invitation is no longer valid.'))
        return redirect('programme_profile_view')

    form = initialize_form(ProgrammeSelfServiceForm, request,
        instance=programme,
        event=event,
        prefix='needs',
    )

    sired_invitation_formset = get_sired_invitation_formset(request, invitation)

    if request.method == 'POST':
        if form.is_valid() and sired_invitation_formset.is_valid():
            with transaction.atomic():
                programme_role = invitation.accept(request.user.person)
                programme = form.save()

                for extra_invite in sired_invitation_formset.save(commit=False):
                    extra_invite.programme = programme
                    extra_invite.created_by = request.user
                    extra_invite.role = invitation.role
                    extra_invite.sire = programme_role
                    extra_invite.save()
                    extra_invite.send(request)

            programme.apply_state()

            messages.success(request, _(
                'Thank you for accepting the invitation. You can change the '
                'information later from your profile.'
            ))

            return redirect('programme_profile_detail_view', programme.pk)
        else:
            messages.error(request, _('Please check the form.'))

    vars = dict(
        form=form,
        freeform_organizers=FreeformOrganizer.objects.filter(programme=programme),
        host_can_invite_more=invitation.extra_invites > 0,
        invitation=invitation,
        invitations=Invitation.objects.filter(programme=programme, state='valid').exclude(pk=invitation.pk),
        sired_invitation_formset=sired_invitation_formset,
        programme_roles=ProgrammeRole.objects.filter(programme=programme),
    )

    return render(request, 'programme_accept_invitation_view.jade', vars)