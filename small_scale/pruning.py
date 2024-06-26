import torch

def prune_vggnet_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune vggnet weights based on pruning information"""
    in_saved_idxs = [0,1,2]
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
        pruned_conv_weight = origin_state_dict[f"{conv_layer}.weight"][out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_conv_bias = origin_state_dict[f"{conv_layer}.bias"][out_saved_idxs]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        pruned_state_dict[f"{conv_layer}.bias"] = pruned_conv_bias
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][out_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
        in_saved_idxs = out_saved_idxs
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,in_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    bn_params = ["bias", "running_mean", "running_var", "weight"]
    for bn_param in bn_params:
        pruned_state_dict[f"classifier.norm.{bn_param}"] = origin_state_dict[f"classifier.norm.{bn_param}"]
    return pruned_state_dict

def prune_resnet_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune resnet weights based on pruning information"""
    in_saved_idxs, out_saved_idxs = [0,1,2], None
    last_downsample_out_saved_idxs = prune_info["conv"]["saved_idxs"]
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        downsample_layer = "conv" if ("layer1" in conv_layer or conv_layer == "conv") else f"{conv_layer.split('.')[0]}.0.downsample.0"
        downsample_out_saved_idxs = prune_info[downsample_layer]["saved_idxs"]
        if "layer" in conv_layer and "conv2" in conv_layer:
            in_saved_idxs = prune_info[conv_layer.replace("conv2", "conv1")]["saved_idxs"]
            out_saved_idxs = downsample_out_saved_idxs
        elif "downsample" in conv_layer:
            in_saved_idxs = last_downsample_out_saved_idxs
            out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
            last_downsample_out_saved_idxs = downsample_out_saved_idxs
        else:
            out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
        pruned_conv_weight = origin_state_dict[f"{conv_layer}.weight"][out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][out_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
        in_saved_idxs = downsample_out_saved_idxs
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,in_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    return pruned_state_dict

def prune_densenet_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune densenet weights based on pruning information"""
    in_saved_idxs, last_in_saved_idxs = [0,1,2], []
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
        origin_conv_weight = origin_state_dict[f"{conv_layer}.weight"]
        pruned_conv_weight = origin_conv_weight[out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        if conv_layer == "conv" or "trans" in conv_layer:
            in_saved_idxs = out_saved_idxs
            last_in_saved_idxs = out_saved_idxs
        else:
            offset = list((torch.tensor(out_saved_idxs)+origin_conv_weight.shape[1]).cpu().numpy())
            in_saved_idxs = last_in_saved_idxs + offset
            last_in_saved_idxs = in_saved_idxs
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][in_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,in_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    return pruned_state_dict

def prune_googlenet_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune googlenet weights based on pruning information"""
    in_saved_idxs, cat_saved_idxs = [0,1,2], []
    offset, next_cat_saved_idxs = 0, []
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
        origin_conv_weight = origin_state_dict[f"{conv_layer}.weight"]
        pruned_conv_weight = origin_conv_weight[out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][out_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
        if conv_layer == "pre_layers.0":
            cat_saved_idxs = out_saved_idxs
            in_saved_idxs = out_saved_idxs
        elif ".".join(conv_layer.split(".")[1:]) in ["b1.0", "b2.3", "b3.6"]:
            in_saved_idxs = cat_saved_idxs
            next_cat_saved_idxs += list((torch.tensor(out_saved_idxs)+offset).cpu().numpy())
            offset += origin_conv_weight.shape[0]   
        elif "b4.1" in conv_layer:
            next_cat_saved_idxs += list((torch.tensor(out_saved_idxs)+offset).cpu().numpy())
            cat_saved_idxs = next_cat_saved_idxs
            in_saved_idxs = next_cat_saved_idxs
            offset, next_cat_saved_idxs = 0, []
        else:
            in_saved_idxs  = out_saved_idxs
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,in_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    return pruned_state_dict

def prune_mobilenet_v1_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune mobilenet_v1 weights based on pruning information"""
    in_saved_idxs, out_saved_idxs = [0,1,2], None
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        if conv_layer == "model.0.0" or conv_layer.split(".")[2] == "3":
            out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
        pruned_conv_weight = origin_state_dict[f"{conv_layer}.weight"][out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][out_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
        if conv_layer == "model.0.0" or conv_layer.split(".")[2] == "3":
            in_saved_idxs = [0]
        else:
            in_saved_idxs = out_saved_idxs
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,out_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    return pruned_state_dict

def prune_mobilenet_v2_weights(prune_info, pruned_state_dict, origin_state_dict, conv_layers, bn_layers, linear_layers):
    """prune mobilenet_v2 weights based on pruning information"""
    in_saved_idxs, out_saved_idxs, next_block_in_saved_idxs = [0,1,2], None, None
    for conv_layer, bn_layer in zip(conv_layers, bn_layers):
        if ((conv_layer in ["conv1", "conv2"]) or ("shortcut" in conv_layer) or ("conv1" in conv_layer)
            or (("conv3" in conv_layer) and (conv_layer.split(".")[1] in ["3", "6", "13"]))):
            out_saved_idxs = prune_info[conv_layer]["saved_idxs"]
            if not("conv1" != conv_layer and "conv1" in conv_layer):
                next_block_in_saved_idxs = out_saved_idxs
        elif "conv3" in conv_layer:
            shortcut_layer = conv_layer.replace("conv3", "shortcut.0")
            out_saved_idxs = prune_info[shortcut_layer]["saved_idxs"]
        pruned_conv_weight = origin_state_dict[f"{conv_layer}.weight"][out_saved_idxs,:,:,:][:,in_saved_idxs,:,:]
        pruned_state_dict[f"{conv_layer}.weight"] = pruned_conv_weight
        bn_params = ["bias", "running_mean", "running_var", "weight"]
        for bn_param in bn_params:
            pruned_bn_param = origin_state_dict[f"{bn_layer}.{bn_param}"][out_saved_idxs]
            pruned_state_dict[f"{bn_layer}.{bn_param}"] = pruned_bn_param
        if "layers" in conv_layer and "conv1" in conv_layer:
            in_saved_idxs = [0]
        elif "conv3" in conv_layer:
            in_saved_idxs = next_block_in_saved_idxs
        else:
            in_saved_idxs = out_saved_idxs
    for i, linear_layer in enumerate(linear_layers):
        if i == 0:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"][:,in_saved_idxs]
        else:
            pruned_state_dict[f"{linear_layer}.weight"] = origin_state_dict[f"{linear_layer}.weight"]
        pruned_state_dict[f"{linear_layer}.bias"] = origin_state_dict[f"{linear_layer}.bias"]
    return pruned_state_dict