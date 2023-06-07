from pynetdicom import AE, debug_logger
from pydicom import dcmread


debug_logger()

ae = AE(ae_title=b'CONRADCL')
ae.add_requested_context('1.2.840.10008.5.1.4.1.1.1')
file = '1.2.826.0.1.3680043.8.498.11775413763338931293083131518365818130.dcm'
ds = dcmread(file)
# ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
assoc = ae.associate('10.8.0.1', 11112, ae_title=b'DCM4CHEE')
if assoc.is_established:
    for cx in assoc.accepted_contexts:
        cx._as_scp = True
    # Use the C-STORE service to send the dataset
    # returns the response status as a pydicom Dataset
    status = assoc.send_c_store(ds)

    # Check the status of the storage request
    if status:
        # If the storage request succeeded this will be 0x0000
        print('C-STORE request status: 0x{0:04x}'.format(status.Status))
    else:
        print('Connection timed out, was aborted or received invalid response')

    # Release the association
    assoc.release()
else:
    print('Association rejected, aborted or never connected')
