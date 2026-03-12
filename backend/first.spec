Model Smartrecon {
    name str minlen=3 maxlen=256
    description str
    
    Config=> {
	collection_name=test
}
}

Model ReconExecDetailsLog {
	reconId str

	Config=> {
	    collection_name=recon_execution_details_log
}
}
