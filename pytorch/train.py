import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from time import time

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def eval_sample(model, sample, loss_fn=nn.MSELoss()):
    label, *data = [torch.from_numpy(d).to(DEVICE) for d in sample]
    pred = model(*data)
    loss = loss_fn(pred, label)
    return loss

def train(model, g_reader, n_epoch, 
            start_lr=0.0003, decay_steps=10, decay_rate=0.96, 
            display_epoch=1, ckpt_file=None):
    optimizer = optim.Adam(model.parameters(), lr=start_lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, decay_steps, decay_rate)
    loss_fn = nn.MSELoss()

    print("# working on device:", DEVICE)
    print("# epoch      trn_err   tst_err        lr  trn_time  tst_time ")
    tic = time()
    trn_loss = eval_sample(model, g_reader.sample_train()).item()
    tst_loss = eval_sample(model, g_reader.sample_all()).item()
    tst_time = time() - tic
    print(f"  {0:<8d}  {np.sqrt(trn_loss):>.2e}  {np.sqrt(tst_loss):>.2e}  {start_lr:>.2e}  {0:>8.2f}  {tst_time:>8.2f}")

    for epoch in range(1, n_epoch+1):
        tic = time()
        for sample in g_reader:
            label, *data = [torch.from_numpy(d).to(DEVICE) for d in sample]
            optimizer.zero_grad()
            pred = model(*data)
            loss = loss_fn(pred, label)
            loss.backward()
            optimizer.step()

        if epoch % display_epoch == 0:
            trn_loss = loss.item()
            trn_time = time() - tic
            tic = time()
            tst_loss = eval_sample(model, g_reader.sample_all()).item()
            tst_time = time() - tic
            print(f"  {epoch:<8d}  {np.sqrt(trn_loss):>.2e}  {np.sqrt(tst_loss):>.2e}  {scheduler.get_lr()[0]:>.2e}  {trn_time:>8.2f}  {tst_time:8.2f}")
        if ckpt_file:
            torch.save(model.state_dict(), ckpt_file)
        
        scheduler.step()


if __name__ == "__main__":
    from model import QCNet
    from reader import GroupReader
    model = QCNet([5,10,10], [120,120,120]).double().to(DEVICE)
    g_reader = GroupReader(["/data1/yixiaoc/work/deep.qc/data/wanghan/data_B_B"], 32)
    train(model, g_reader, 10)