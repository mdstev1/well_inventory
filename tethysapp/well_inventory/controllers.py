from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from django.utils.html import format_html
from tethys_sdk.permissions import login_required, permission_required, has_permission
from tethys_sdk.gizmos import MapView, Button, TextInput, DatePicker, SelectInput, DataTableView, MVDraw, MVView, MVLayer
from tethys_sdk.workspaces import app_workspace

from .model import add_new_well, get_all_wells, assign_hydrograph_to_well, Well, get_hydrograph
from .app import WellInventory as app
from .helpers import create_hydrograph

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
        layer_options={'style': style},
        feature_selection=True
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
        'add_well_button': add_well_button,
        'can_add_wells': has_permission(request, 'add_wells')
    }

    return render(request, 'well_inventory/home.html', context)




@permission_required('add_wells')
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
        display_text='river',
        name='river',
        placeholder='e.g.: Colorado Plateaus',
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
        'can_add_wells': has_permission(request, 'add_wells'),
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
        hydrograph_id = get_hydrograph(well.id)
        if hydrograph_id:
            url = reverse('well_inventory:hydrograph', kwargs={'hydrograph_id': hydrograph_id})
            well_hydrograph = format_html('<a class="btn btn-primary" href="{}">Hydrograph Plot</a>'.format(url))
        else:
            well_hydrograph = format_html('<a class="btn btn-primary disabled" title="No hydrograph assigned" '
                                         'style="pointer-events: auto;">Hydrograph Plot</a>')
        table_rows.append(
            (
                well.name, well.owner,
                well.river, well.date_built,
                well_hydrograph
            )
        )

    wells_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built', 'Hydrograph'),
        rows=table_rows,
        searching=False,
        orderClasses=False,
        lengthMenu=[[10, 25, 50, -1], [10, 25, 50, "All"]],
    )

    context = {
        'wells_table': wells_table,
        'can_add_wells': has_permission(request, 'add_wells')
    }

    return render(request, 'well_inventory/list_wells.html', context)


@login_required()
def assign_hydrograph(request):
    """
    Controller for the Add Hydrograph page.
    """
    # Get wells from database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    all_wells = session.query(Well).all()

    # Defaults
    well_select_options = [(well.name, well.id) for well in all_wells]
    selected_well = None
    hydrograph_file = None

    # Errors
    well_select_errors = ''
    hydrograph_file_error = ''

    # Case where the form has been submitted
    if request.POST and 'add-button' in request.POST:
        # Get Values
        has_errors = False
        selected_well = request.POST.get('well-select', None)

        if not selected_well:
            has_errors = True
            well_select_errors = 'Well is Required.'

        # Get File
        if request.FILES and 'hydrograph-file' in request.FILES:
            # Get a list of the files
            hydrograph_file = request.FILES.getlist('hydrograph-file')

        if not hydrograph_file and len(hydrograph_file) > 0:
            has_errors = True
            hydrograph_file_error = 'Hydrograph File is Required.'

        if not has_errors:
            # Process file here
            success = assign_hydrograph_to_well(selected_well, hydrograph_file[0])

            # Provide feedback to user
            if success:
                messages.info(request, 'Successfully assigned hydrograph.')
            else:
                messages.info(request, 'Unable to assign hydrograph. Please try again.')
            return redirect(reverse('well_inventory:home'))

        messages.error(request, "Please fix errors.")

    well_select_input = SelectInput(
        display_text='Well',
        name='well-select',
        multiple=False,
        options=well_select_options,
        initial=selected_well,
        error=well_select_errors
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'add-hydrograph-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('well_inventory:home')
    )

    context = {
        'well_select_input': well_select_input,
        'hydrograph_file_error': hydrograph_file_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
        'can_add_wells': has_permission(request, 'add_wells')
    }

    session.close()

    return render(request, 'well_inventory/assign_hydrograph.html', context)

@login_required()
def hydrograph(request, hydrograph_id):
    """
    Controller for the Hydrograph Page.
    """
    hydrograph_plot = create_hydrograph(hydrograph_id)

    context = {
        'hydrograph_plot': hydrograph_plot,
        'can_add_wells': has_permission(request, 'add_wells')
    }
    return render(request, 'well_inventory/hydrograph.html', context)

@login_required()
def hydrograph_ajax(request, well_id):
    """
    Controller for the Hydrograph Page.
    """
    # Get wells from database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    well = session.query(Well).get(int(well_id))

    if well.hydrograph:
        hydrograph_plot = create_hydrograph(well.hydrograph.id, height='300px')
    else:
        hydrograph_plot = None

    context = {
        'hydrograph_plot': hydrograph_plot,
    }

    session.close()
    return render(request, 'well_inventory/hydrograph_ajax.html', context)

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

