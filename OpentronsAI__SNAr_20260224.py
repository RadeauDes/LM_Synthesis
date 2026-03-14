from opentrons import protocol_api

metadata = {
    'protocolName': 'SNAr Reaction Protocol - Multi-Plate Transfer',
    'author': 'OpentronsAI',
    'description': 'Transfer amines to electrophiles across 3 plates with timed additions and mixing',
    'source': 'OpentronsAI'
}

requirements = {
    'robotType': 'Flex',
    'apiLevel': '2.25'
}

def add_parameters(parameters):
    parameters.add_str(
        variable_name='pipette_1ch_mount',
        display_name='1-Channel Pipette Mount',
        description='Mount position for 1-channel pipette',
        choices=[
            {'display_name': 'Left', 'value': 'left'},
            {'display_name': 'Right', 'value': 'right'}
        ],
        default='left'
    )
    
    parameters.add_str(
        variable_name='pipette_8ch_mount',
        display_name='8-Channel Pipette Mount',
        description='Mount position for 8-channel pipette',
        choices=[
            {'display_name': 'Left', 'value': 'left'},
            {'display_name': 'Right', 'value': 'right'}
        ],
        default='right'
    )

def run(protocol: protocol_api.ProtocolContext):
    # Access runtime parameters
    mount_1ch = protocol.params.pipette_1ch_mount
    mount_8ch = protocol.params.pipette_8ch_mount
    
    # Load trash bin
    trash = protocol.load_trash_bin('A3')
    
    # Load labware - need multiple tip racks for all the transfers
    tiprack_50ul_1 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D1')
    tiprack_50ul_2 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D2')
    tiprack_50ul_3 = protocol.load_labware('opentrons_flex_96_filtertiprack_50ul', 'D3')
    
    plate_1_amine = protocol.load_labware('axygen_96_wellplate_500ul', 'C1', 'Amine Plate')
    plate_2_electrophile = protocol.load_labware('axygen_96_wellplate_500ul', 'C2', 'Electrophile Plate 2')
    plate_3_electrophile = protocol.load_labware('axygen_96_wellplate_500ul', 'B1', 'Electrophile Plate 3')
    plate_4_electrophile = protocol.load_labware('axygen_96_wellplate_500ul', 'B2', 'Electrophile Plate 4')
    
    # Load pipettes
    pipette_1ch = protocol.load_instrument(
        'flex_1channel_50',
        mount=mount_1ch,
        tip_racks=[tiprack_50ul_1, tiprack_50ul_2, tiprack_50ul_3]
    )
    
    pipette_8ch = protocol.load_instrument(
        'flex_8channel_50',
        mount=mount_8ch,
        tip_racks=[tiprack_50ul_1, tiprack_50ul_2, tiprack_50ul_3]
    )
    
    # Define liquids
    amine_liquid = protocol.define_liquid(
        name='Amine',
        description='Viscous amine solution for SNAr reaction',
        display_color='#00FF00'
    )
    
    electrophile_liquid = protocol.define_liquid(
        name='Electrophile',
        description='Electrophile solution for SNAr reaction',
        display_color='#FF0000'
    )
    
    # Load liquids into labware
    for well in plate_1_amine.columns()[0]:
        well.load_liquid(liquid=amine_liquid, volume=125)  # 25 µL × 5 transfers
    
    for well in plate_2_electrophile.wells():
        well.load_liquid(liquid=electrophile_liquid, volume=50)
    for well in plate_3_electrophile.wells():
        well.load_liquid(liquid=electrophile_liquid, volume=50)
    for well in plate_4_electrophile.wells():
        well.load_liquid(liquid=electrophile_liquid, volume=50)
    
    # Set flow rates to 5 µL/s for aspirate and dispense (viscous liquid)
    pipette_8ch.flow_rate.aspirate = 5
    pipette_8ch.flow_rate.dispense = 5
    
    # Source column (column 1 of plate 1, 8 amines A-H)
    source_column = plate_1_amine.columns()[0]
    
    # Destination columns for each plate
    plate_2_dest_cols = plate_2_electrophile.columns()[0:2]  # Columns 1-2
    plate_3_dest_cols = plate_3_electrophile.columns()[0:3]  # Columns 1-3
    plate_4_dest_cols = plate_4_electrophile.columns()[0:2]  # Columns 1-2
    
    # Combine all destination columns in order
    all_dest_cols = plate_2_dest_cols + plate_3_dest_cols + plate_4_dest_cols
    
    # Perform 5 transfers of 5 µL each
    for transfer_num in range(1, 6):
        protocol.comment(f'Starting transfer {transfer_num} of 5 (5 µL each)')
        
        # Determine if this is the final transfer (for mixing)
        is_final_transfer = (transfer_num == 5)
        
        # Transfer to all destination columns
        for dest_col in all_dest_cols:
            if is_final_transfer:
                # Final transfer: mix 2x with 40 µL at 10 µL/s, then blowout
                pipette_8ch.pick_up_tip()
                pipette_8ch.aspirate(5, source_column[0])
                pipette_8ch.dispense(5, dest_col[0])
                pipette_8ch.blow_out(dest_col[0])
                
                # Set mixing flow rate to 10 µL/s
                pipette_8ch.flow_rate.aspirate = 10
                pipette_8ch.flow_rate.dispense = 10
                pipette_8ch.mix(2, 40, dest_col[0])
                
                # Reset flow rates back to 5 µL/s
                pipette_8ch.flow_rate.aspirate = 5
                pipette_8ch.flow_rate.dispense = 5
                
                pipette_8ch.drop_tip()
            else:
                # Regular transfer with blowout
                pipette_8ch.transfer(
                    5,
                    source_column[0],
                    dest_col[0],
                    blow_out=True,
                    blowout_location='destination well',
                    new_tip='always'
                )
        
        # Wait 10 minutes after each transfer set (except after the last one)
        if not is_final_transfer:
            protocol.comment(f'Waiting 10 minutes before transfer {transfer_num + 1}')
            protocol.delay(minutes=10)
    
    protocol.comment('Protocol complete! Total of 25 µL transferred to each well.')