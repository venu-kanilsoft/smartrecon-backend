Model Glmapping {
    reconName str
    reconProcess str
    reconId str
    glNumber str
    glName str
    Action=> gluploadinputdata {
        recon_id str
    }
    Config=> {
        collection_name=gl_mapping
    }
}