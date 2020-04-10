from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from tethys_sdk.permissions import login_required
from tethys_sdk.gizmos import MapView, Button, TextInput, DatePicker, SelectInput, DataTableView, MVDraw, MVView, MVLayer
from tethys_sdk.workspaces import app_workspace
from .model import add_new_well, get_all_wells


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    # Get list of wells and create wells MVLayer:
    wells = get_all_wells()
    features = []
    lat_list = []
    lng_list = []

    for well in wells:
        lat_list.append(well.latitude)
        lng_list.append(well.longitude)

        well_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [well.longitude, well.latitude],
            },
            'properties': {
                'id': well.id,
                'name': well.name,
                'owner': well.owner,
                'river': well.river,
                'date_built': well.date_built
            }
        }

        features.append(well_feature)

    # Define GeoJSON FeatureCollection
    wells_feature_collection = {
        'type': 'FeatureCollection',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:4326'
            }
        },
        'features': features
    }

    style = {'ol.style.Style': {
        'image': {'ol.style.Circle': {
            'radius': 10,
            'fill': {'ol.style.Fill': {
                'color':  '#d84e1f'
            }},
            'stroke': {'ol.style.Stroke': {
                'color': '#ffffff',
                'width': 1
            }}
        }}
    }}

    # Create a Map View Layer
    wells_layer = MVLayer(
        source='GeoJSON',
        options=wells_feature_collection,
        legend_title='Wells',
        layer_options={'style': style}
    )

    # Define view centered on well locations
    try:
        view_center = [sum(lng_list) / float(len(lng_list)), sum(lat_list) / float(len(lat_list))]
    except ZeroDivisionError:
        view_center = [-98.6, 39.8]

    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=4.5,
        maxZoom=18,
        minZoom=2
    )

    well_inventory_map = MapView(
        height='100%',
        width='100%',
        layers=[wells_layer],
        basemap='OpenStreetMap',
        view=view_options
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
    # Default Values
    name = ''
    owner = 'Reclamation'
    river = ''
    date_built = ''
    location = ''

    # Errors
    name_error = ''
    owner_error = ''
    river_error = ''
    date_error = ''
    location_error = ''

    # Handle form submission
    if request.POST and 'add-button' in request.POST:
        # Get values
        has_errors = False
        name = request.POST.get('name', None)
        owner = request.POST.get('owner', None)
        river = request.POST.get('river', None)
        date_built = request.POST.get('date-built', None)
        location = request.POST.get('geometry', None)

        # Validate
        if not name:
            has_errors = True
            name_error = 'Name is required.'

        if not owner:
            has_errors = True
            owner_error = 'Owner is required.'

        if not river:
            has_errors = True
            river_error = 'River is required.'

        if not date_built:
            has_errors = True
            date_error = 'Date Built is required.'

        if not location:
            has_errors = True
            location_error = 'Location is required.'

        if not has_errors:
            add_new_well(location=location, name=name, owner=owner, river=river, date_built=date_built)
            return redirect(reverse('well_inventory:home'))

        messages.error(request, "Please fix errors.")

    # Define form gizmos
    name_input = TextInput(
        display_text='Name',
        name='name',
        initial=name,
        error=name_error
    )

    owner_input = SelectInput(
        display_text='Owner',
        name='owner',
        multiple=False,
        options=[('Reclamation', 'Reclamation'), ('Army Corp', 'Army Corp'), ('Other', 'Other')],
        initial=owner,
        error=owner_error
    )

    river_input = TextInput(
        display_text='River',
        name='river',
        placeholder='e.g.: Mississippi River',
        initial=river,
        error=river_error
    )

    date_built = DatePicker(
        name='date-built',
        display_text='Date Built',
        autoclose=True,
        format='MM d, yyyy',
        start_view='decade',
        today_button=True,
        initial=date_built,
        error=date_error
    )

    initial_view = MVView(
        projection='EPSG:4326',
        center=[-98.6, 39.8],
        zoom=3.5
    )

    drawing_options = MVDraw(
        controls=['Modify', 'Delete', 'Move', 'Point'],
        initial='Point',
        output_format='GeoJSON',
        point_color='#FF0000'
    )

    location_input = MapView(
        height='300px',
        width='100%',
        basemap='OpenStreetMap',
        draw=drawing_options,
        view=initial_view
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'add-well-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('well_inventory:home')
    )

    context = {
        'name_input': name_input,
        'owner_input': owner_input,
        'river_input': river_input,
        'date_built_input': date_built,
        'location_input': location_input,
        'location_error': location_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
    }

    return render(request, 'well_inventory/add_well.html', context)


@login_required()
def list_wells(request):
    """
    Show all wells in a table view.
    """
    wells = get_all_wells()
    table_rows = []

    for well in wells:
        table_rows.append(
            (
                well.name, well.owner,
                well.river, well.date_built
            )
        )

    wells_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built'),
        rows=table_rows,
        searching=False,
        orderClasses=False,
        lengthMenu=[[10, 25, 50, -1], [10, 25, 50, "All"]],
    )

    context = {
        'wells_table': wells_table
    }

    return render(request, 'well_inventory/list_wells.html', context)









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

