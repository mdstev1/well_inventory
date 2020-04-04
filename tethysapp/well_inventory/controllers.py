from django.shortcuts import render, reverse
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import MapView, Button

@login_required()
def home(request):
    """
    Controller for the app home page.
    """

    well_inventory_map = MapView(
        height='100%',
        width='100%',
        layers=[],
        basemap='OpenStreetMap',
    )

    add_well_button = Button(
        display_text='Add Well',
        name='add-well-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        href=reverse('well_inventory:add_well')
    )

    context = {
        'well_inventory_map': well_inventory_map,
        'add_well_button': add_well_button
    }

    return render(request, 'well_inventory/home.html', context)

@login_required()
def add_well(request):
    """
    Controller for the Add Well page.
    """
    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success'
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('well_inventory:home')
    )

    context = {
        'add_button': add_button,
        'cancel_button': cancel_button,
    }
    return render(request, 'well_inventory/add_well.html', context)

    # save_button = Button(
    #     display_text='',
    #     name='save-button',
    #     icon='glyphicon glyphicon-floppy-disk',
    #     style='success',
    #     attributes={
    #         'data-toggle':'tooltip',
    #         'data-placement':'top',
    #         'title':'Save'
    #     }
    # )
    #
    # edit_button = Button(
    #     display_text='',
    #     name='edit-button',
    #     icon='glyphicon glyphicon-edit',
    #     style='warning',
    #     attributes={
    #         'data-toggle':'tooltip',
    #         'data-placement':'top',
    #         'title':'Edit'
    #     }
    # )
    #
    # remove_button = Button(
    #     display_text='',
    #     name='remove-button',
    #     icon='glyphicon glyphicon-remove',
    #     style='danger',
    #     attributes={
    #         'data-toggle':'tooltip',
    #         'data-placement':'top',
    #         'title':'Remove'
    #     }
    # )
    #
    # previous_button = Button(
    #     display_text='Previous',
    #     name='previous-button',
    #     attributes={
    #         'data-toggle':'tooltip',
    #         'data-placement':'top',
    #         'title':'Previous'
    #     }
    # )
    #
    # next_button = Button(
    #     display_text='Next',
    #     name='next-button',
    #     attributes={
    #         'data-toggle':'tooltip',
    #         'data-placement':'top',
    #         'title':'Next'
    #     }
    # )
    #
    # context = {
    #     'save_button': save_button,
    #     'edit_button': edit_button,
    #     'remove_button': remove_button,
    #     'previous_button': previous_button,
    #     'next_button': next_button
    # }

