using System;
using System.Collections.Generic;
using System.Collections;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.IO;
using System.Globalization;

namespace ReadingOffsets
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }


        public static class MyGlobals
        {
            //magicnumber is "RTDP" = 52544450 in hex
            public static byte[] magicnumber = { 0x52, 0x54, 0x44, 0x50 };

            //end of the header
            public static byte[] EndOfHeader = new byte[4];
            
            //number of files
            public static byte[] NumberOfFiles = new byte[4];
            
            //filesize
            public static byte[] VolFilesize = new byte[4];
            
            //XOR-key
            public static byte XORkey = 0;
            
            //unknown bytes after the xorvalue
            public static byte[] UNKbytes = new byte[4];

            //infos about the files in the volarchive
            public static byte[][] VolFileInfos;

            //path of the volarchive
            public static string VolFilepath;
        }

        //method to convert a bytearray to an integervalue (bigendian)
        public static int longBytearrayToInterger(byte[] array)
        {
            byte[] temp = new byte[4];
            Array.Copy(array, temp, 4);
            Array.Reverse(temp);
            Int32 IntegerValue = BitConverter.ToInt32(temp, 0);
            return IntegerValue;
        }

        private void OpenVolButton_Click(object sender, EventArgs e)
        {
            //magicnumber is "RTDP" = 52544450 in hex
            //byte[] magicnumber = new byte[] { 0x52, 0x54, 0x44, 0x50 };
            //byte[] magicnumber = { 0x52, 0x54, 0x44, 0x50 };
            byte[] temp;
            string path = string.Empty;
            
            OpenFileDialog OpenVolFile = new OpenFileDialog();
            OpenVolFile.Filter = "vol (*.vol)|*.vol";

            if (OpenVolFile.ShowDialog() == DialogResult.OK)
            {
                MyGlobals.VolFilepath = OpenVolFile.FileName;
                path = OpenVolFile.FileName;
                BinaryReader ReadBinary = new BinaryReader(File.Open(@path, FileMode.Open));

                //read magicnumber from file and validate filetype by comparing to the given magicnumber
                temp = ReadBinary.ReadBytes(4);

                for (int i = 0; i < 4; i++)
                {
                    if (temp[i] == MyGlobals.magicnumber[i])
                    {
                        //set name of the window/form to the one of the choosen filename
                        this.Text = OpenVolFile.SafeFileName;
                    }
                    else
                    {
                        MessageBox.Show("This is not a valid .vol-archive (RTDP)");
                    }
                }
                //read the end of the header and write it to the logbox
                MyGlobals.EndOfHeader = ReadBinary.ReadBytes(4);
                TextLogBox.Text = "EndOfHeader HEX: " + System.BitConverter.ToString(MyGlobals.EndOfHeader) + Environment.NewLine;
                TextLogBox.AppendText("EndOfHeader DEC: " + longBytearrayToInterger(MyGlobals.EndOfHeader) + Environment.NewLine);
                //read the number of files and write it to the logbox
                MyGlobals.NumberOfFiles = ReadBinary.ReadBytes(4);
                TextLogBox.AppendText("NumberOfFiles HEX: " + System.BitConverter.ToString(MyGlobals.NumberOfFiles) + Environment.NewLine);
                TextLogBox.AppendText("NumberOfFiles DEC: " + longBytearrayToInterger(MyGlobals.NumberOfFiles) + Environment.NewLine);
                //read the filesize and write it to the logbox
                MyGlobals.VolFilesize = ReadBinary.ReadBytes(4);
                TextLogBox.AppendText("VolFilesize HEX: " + System.BitConverter.ToString(MyGlobals.VolFilesize) + Environment.NewLine);
                TextLogBox.AppendText("VolFilesize DEC: " + longBytearrayToInterger(MyGlobals.VolFilesize) + Environment.NewLine);
                //read the XOR-key and write it to the logbox
                MyGlobals.XORkey = ReadBinary.ReadByte();
                TextLogBox.AppendText("XORkey HEX: " + String.Format("{0:X}", MyGlobals.XORkey) + Environment.NewLine);
                TextLogBox.AppendText("XORkey DEC: " + MyGlobals.XORkey + Environment.NewLine);
                //read some unknown bytes after the xorvalue
                MyGlobals.UNKbytes = ReadBinary.ReadBytes(4);
                TextLogBox.AppendText("UNKbytes HEX: " + System.BitConverter.ToString(MyGlobals.UNKbytes) + Environment.NewLine);
                TextLogBox.AppendText("UNKbytes DEC: " + longBytearrayToInterger(MyGlobals.UNKbytes) + Environment.NewLine);

                //goto 0x20, start of filelist
                ReadBinary.BaseStream.Seek(0x20, SeekOrigin.Begin);
                int decNumberOfFiles = longBytearrayToInterger(MyGlobals.NumberOfFiles);
                //reading fileinfos (name 32, size 4, offset 4) in one extra array for every file
                MyGlobals.VolFileInfos = new byte[decNumberOfFiles][];
                for (int i = 0; i < decNumberOfFiles; i++)
                {
                    //read the filename and size and offset
                    MyGlobals.VolFileInfos[i] = ReadBinary.ReadBytes(40);
                }

                //close the binaryreader
                ReadBinary.Close();

                //create a treeview
                FileTree.BeginUpdate();
                FileTree.Nodes.Clear();
                FileTree.Nodes.Add(OpenVolFile.SafeFileName);
                for (int i = 0; i < decNumberOfFiles; i++)
                {
                    //save only the 32 bytes of the filename to a temporary array and get the filepath from there
                    byte[] bTempFilename = new byte[32];
                    Array.Copy(MyGlobals.VolFileInfos[i], bTempFilename, 32);
                    string TempFilename = System.Text.Encoding.ASCII.GetString(bTempFilename);
                    FileTree.Nodes[0].Nodes.Add(TempFilename);
                }
                FileTree.EndUpdate();
                //enable the extract all button if file was loaded
                ExtractAll.Enabled = true;
            }
        }

        private void ContextMenuTreeView_Opening(object sender, CancelEventArgs e)
        {
            //check for an empty treeview and en/disable the menu
            if (FileTree.TopNode == null)
            {
                extractFileToolStripMenuItem.Enabled = false;
                importFileToolStripMenuItem.Enabled = false;
            }
            else
            {
                extractFileToolStripMenuItem.Enabled = true;
                importFileToolStripMenuItem.Enabled = true;
                //check for selected topnode and disable the menu for ectraction if it has no parent
                if (FileTree.SelectedNode.Parent == null)
                {
                    extractFileToolStripMenuItem.Enabled = false;
                    importFileToolStripMenuItem.Enabled = false;
                }
            }
        }

        private void FileTree_NodeMouseClick(object sender, TreeNodeMouseClickEventArgs e)
        {
            //on rightclick in the treeview select the rightclicked node
            TreeNode selectedNode =  FileTree.GetNodeAt(e.X, e.Y);
            if (e.Button == MouseButtons.Right)
            {
                FileTree.SelectedNode = selectedNode;
            }
        }

        private void extractFileToolStripMenuItem_Click(object sender, EventArgs e)
        {
            // Displays a SaveFileDialog
            string extractfilename = System.Text.Encoding.ASCII.GetString(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index]).Remove(32);
            SaveFileDialog saveFileDialog1 = new SaveFileDialog();
            saveFileDialog1.FileName = extractfilename;
            saveFileDialog1.Title = "Save as...";
            // If the file name is not an empty string open it for saving.
            if (saveFileDialog1.FileName != "" && saveFileDialog1.ShowDialog() == DialogResult.OK)
            {
                //create binarywriter
                using (BinaryWriter binWriter = new BinaryWriter(File.Open(saveFileDialog1.FileName, FileMode.Create)))
                {
                    //make extra variables to save the filesize and offset of the file to extract
                    byte[] exFilesize = new byte[4];
                    byte[] exFileoffset = new byte[4];
                    Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 32, exFilesize, 0, 4);
                    Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, exFileoffset, 0, 4);
                    //add endofheader to the fileoffset
                    int realoff = longBytearrayToInterger(exFileoffset) + longBytearrayToInterger(MyGlobals.EndOfHeader);
                    exFileoffset = System.BitConverter.GetBytes(realoff);
                    Array.Reverse(exFileoffset); //freaking bitconvert is giving littleendian values back...
                    //make a buffer of the size of the file to extract
                    byte[] exFilebuffer = new byte[longBytearrayToInterger(exFilesize)];
                    BinaryReader ReadBinary = new BinaryReader(File.Open(MyGlobals.VolFilepath, FileMode.Open));
                    ReadBinary.BaseStream.Seek(longBytearrayToInterger(exFileoffset), 0);
                    exFilebuffer = ReadBinary.ReadBytes(longBytearrayToInterger(exFilesize));
                    //XOR every byte of the exFilebuffer with the XORkey
                    for(int i = 0; i< exFilebuffer.Length; i++)
                    {
                        exFilebuffer[i] = (byte)(exFilebuffer[i] ^ MyGlobals.XORkey);
                    }
                    //finaly write the file
                    binWriter.Write(exFilebuffer);

                    binWriter.Close();
                    ReadBinary.Close();
                }
                MessageBox.Show("Extraction finished.",extractfilename);
            }
        }

        private void FileTree_AfterSelect(object sender, TreeViewEventArgs e)
        {
            //write some fileinfos for the file to extract to another logbox 
            //check for selected topnode and dont write to the exfilenamebox incase its selected
            if (FileTree.SelectedNode.Parent != null)
            {
                byte[] exFilesize = new byte[4];
                byte[] exFileoffset = new byte[4];
                Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 32, exFilesize, 0, 4);
                Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, exFileoffset, 0, 4);
                TextExfileinfoBox.Clear();
                TextExfileinfoBox.AppendText("Filename: " + System.Text.Encoding.ASCII.GetString(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index]).Remove(32));
                TextExfileinfoBox.AppendText(Environment.NewLine + "Filesize: " + longBytearrayToInterger(exFilesize) + " bytes");
                TextExfileinfoBox.AppendText(Environment.NewLine + "Offset(relative to EOH): " + longBytearrayToInterger(exFileoffset));
            }
        }

        private void importFileToolStripMenuItem_Click(object sender, EventArgs e)
        {
            OpenFileDialog OpenImportFile = new OpenFileDialog();
            OpenImportFile.Filter = "*.*|*.*";
            byte[] importbuffer;
            int importfilesize;
            int impfiledifference;
            string path = string.Empty;

            //read the file to import into a buffer
            if (OpenImportFile.ShowDialog() == DialogResult.OK)
            {
                //save the path in a variable
                path = OpenImportFile.FileName;
                //create binaryreader to read the file to import to an array
                BinaryReader ReadBinary = new BinaryReader(File.Open(@path, FileMode.Open));
                //get filesize of file to import
                var impforfileInfo = new FileInfo(OpenImportFile.FileName);
                importfilesize = (int)impforfileInfo.Length;
                //write file into importbuffer
                importbuffer = ReadBinary.ReadBytes(importfilesize);
                ReadBinary.Close();
                //XOR every byte of the file to import with the XORkey
                for (int i = 0; i < importbuffer.Length; i++)
                {
                    importbuffer[i] = (byte)(importbuffer[i] ^ MyGlobals.XORkey);
                }
                //get the filesize of the original file inside the vol
                byte[] orgFilesize = new byte[4];
                Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 32, orgFilesize, 0, 4);

                //calculate the difference between the old and the new filesize
                impfiledifference = Math.Abs(longBytearrayToInterger(orgFilesize) - importfilesize);

                //rebuild whole vol file if imported file is larger/smaller than the original
                if (importfilesize != longBytearrayToInterger(orgFilesize))
                {
                    //rebiuld the header of the vol file, write the importdata and shift the original data
                    //MessageBox.Show("file to import is not even in size");

                    //build new header (by copieng parts of the old header)
                    byte[] newVolHeader = new byte[longBytearrayToInterger(MyGlobals.EndOfHeader)];
                    Array.Copy(MyGlobals.magicnumber, newVolHeader, 4);
                    Array.Copy(MyGlobals.EndOfHeader, 0, newVolHeader, 4, 4);
                    Array.Copy(MyGlobals.NumberOfFiles, 0, newVolHeader, 8, 4);
                    //change volfilesize accoring to the file to import
                    byte[] newVolFilesize = new byte[4];
                    if (importfilesize < longBytearrayToInterger(orgFilesize))
                    {
                        newVolFilesize = System.BitConverter.GetBytes((longBytearrayToInterger(MyGlobals.VolFilesize) - impfiledifference));
                        Array.Reverse(newVolFilesize);
                        Array.Copy(newVolFilesize, 0, newVolHeader, 12, 4);
                    }
                    else
                    {
                        newVolFilesize = System.BitConverter.GetBytes((longBytearrayToInterger(MyGlobals.VolFilesize) + impfiledifference));
                        Array.Reverse(newVolFilesize);
                        Array.Copy(newVolFilesize, 0, newVolHeader, 12, 4);
                    }
                    newVolHeader[16] = MyGlobals.XORkey;
                    Array.Copy(MyGlobals.UNKbytes, 0, newVolHeader, 17, 4);
                    //fill the space till the filenames starts (0x20) with zero
                    for (int zerocount = 21; zerocount < 0x20; zerocount++)
                    {
                        newVolHeader[zerocount] = 0x0;
                    }
                    //begin to write the filelist to the new header
                    int offsetindex = 0x20;
                    for (int filecount = 0; filecount < longBytearrayToInterger(MyGlobals.NumberOfFiles); filecount++)
                    {
                        //write the data of the old vol file to the new header
                        if (filecount < FileTree.SelectedNode.Index)
                        {
                            //copy the fileinfo to the header (name, size, offset is all in the global VolFileInfos)
                            Array.Copy(MyGlobals.VolFileInfos[filecount], 0, newVolHeader, offsetindex, 40);
                            offsetindex = offsetindex + 0x28;
                        }
                        else
                        {
                            //if filecount == selected node in filetree change the filesize of the old file in the vol
                            if (filecount == FileTree.SelectedNode.Index)
                            {
                                //copy the first 32bytes (name) and increase to offsetindex to write to
                                Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 0, newVolHeader, offsetindex, 32);
                                offsetindex = offsetindex + 0x20;
                                //copy the filesize of the file to import into the new header
                                byte[] impFilesize = new byte[4];
                                impFilesize = System.BitConverter.GetBytes(importfilesize);
                                Array.Reverse(impFilesize);
                                Array.Copy(impFilesize, 0, newVolHeader, offsetindex, 4);
                                offsetindex = offsetindex + 4;
                                //copy the fileoffset to the new header
                                Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, newVolHeader, offsetindex, 4);
                                offsetindex = offsetindex + 4;
                            }
                            else //filecount is higher than selected node
                            {
                                //copy the first 32bytes (name) and increase to offsetindex to write to
                                Array.Copy(MyGlobals.VolFileInfos[filecount], 0, newVolHeader, offsetindex, 32);
                                offsetindex = offsetindex + 0x20;
                                //copy the filesize into the new header
                                Array.Copy(MyGlobals.VolFileInfos[filecount], 32, newVolHeader, offsetindex, 4);
                                offsetindex = offsetindex + 4;
                                //copy the updated fileoffset to the header
                                byte[] newFileoffset = new byte[4];
                                byte[] oldFileoffset = new byte[4];
                                Array.Copy(MyGlobals.VolFileInfos[filecount], 36, oldFileoffset, 0, 4);
                                //add or substract the difference between the imported file and the original to/from the offset 
                                if (importfilesize < longBytearrayToInterger(orgFilesize))
                                {
                                    newFileoffset = System.BitConverter.GetBytes((longBytearrayToInterger(oldFileoffset) - impfiledifference));
                                    Array.Reverse(newFileoffset);
                                    //set the offset to zero if its smaller zero
                                    if(longBytearrayToInterger(newFileoffset)<=0)
                                    {
                                        newFileoffset[0] = 0x0;
                                        newFileoffset[1] = 0x0;
                                        newFileoffset[2] = 0x0;
                                        newFileoffset[3] = 0x0;
                                    }
                                    Array.Copy(newFileoffset, 0, newVolHeader, offsetindex, 4);
                                    offsetindex = offsetindex + 4;
                                }
                                else
                                {
                                    newFileoffset = System.BitConverter.GetBytes((longBytearrayToInterger(oldFileoffset) + impfiledifference));
                                    Array.Reverse(newFileoffset);
                                    Array.Copy(newFileoffset, 0, newVolHeader, offsetindex, 4);
                                    offsetindex = offsetindex + 4;
                                }
                            }
                        }
                    }
                    //write the new header and the actual filedata into a new file open the new file and the old one first
                    FileStream writeStream2 = new FileStream(MyGlobals.VolFilepath + ".imp", FileMode.Create, FileAccess.Write);
                    FileStream readStream = new FileStream(MyGlobals.VolFilepath, FileMode.Open, FileAccess.Read);
                    if (FileTree.SelectedNode.Index == longBytearrayToInterger(MyGlobals.NumberOfFiles) - 1) //if the file to import is the last file in the vol
                    {
                        if (FileTree.SelectedNode.Index > 0) //file to import is the last one but not the first
                        {
                            //write old data and the imported file afterwards
                            //make a buffer for the old data
                            byte[] importFileoffset = new byte[4];
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, importFileoffset, 0, 4);
                            byte[] buffer1 = new byte[longBytearrayToInterger(importFileoffset)];
                            //read the old filedata and copy it to buffer1
                            readStream.Seek(longBytearrayToInterger(MyGlobals.EndOfHeader), 0);
                            readStream.Read(buffer1, 0, buffer1.Length);
                            readStream.Flush();
                            readStream.Close();
                            //write newVolheader, buffer1 and importbuffer to new file
                            writeStream2.Write(newVolHeader, 0, newVolHeader.Length);
                            writeStream2.Write(buffer1, 0, buffer1.Length);
                            writeStream2.Write(importbuffer, 0, importbuffer.Length);
                            writeStream2.Flush();
                            writeStream2.Close();
                        }
                        else //file to import is the last AND the first file (only one file in vol)
                        {
                            //only write the imported file since there are no ohter files
                            //write the newVolheader and the importbuffer to file
                            readStream.Flush();
                            readStream.Close();
                            writeStream2.Write(newVolHeader, 0, newVolHeader.Length);
                            writeStream2.Write(importbuffer, 0, importbuffer.Length);
                            writeStream2.Flush();
                            writeStream2.Close();
                        }
                    }
                    else //file is not the last one
                    {
                        if (FileTree.SelectedNode.Index == 0) //if the file to import is the first file in the vol
                        {
                            //write imported file first than the rest from the old volfile
                            //write the newVolheader and the importbuffer to file
                            writeStream2.Write(newVolHeader, 0, newVolHeader.Length);
                            writeStream2.Write(importbuffer, 0, importbuffer.Length);
                            //write the old data to the file
                            //make a buffer for the old data
                            byte[] ImpFileoffset = new byte[4];
                            byte[] OldimpFilesize = new byte[4];
                            byte[] afterImpOffset = new byte[4];
                            int iafterImpOffset;
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, ImpFileoffset, 0, 4); //get offset of old importfile
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 32, OldimpFilesize, 0, 4); //get size of old importfile
                            iafterImpOffset = longBytearrayToInterger(ImpFileoffset) + longBytearrayToInterger(MyGlobals.EndOfHeader) + longBytearrayToInterger(OldimpFilesize); //calculate offset of the file after the old importfile
                            afterImpOffset = System.BitConverter.GetBytes(iafterImpOffset);
                            Array.Reverse(afterImpOffset);
                            int buffer2lenght = longBytearrayToInterger(MyGlobals.VolFilesize) - longBytearrayToInterger(afterImpOffset);//make buffer the right size
                            if (buffer2lenght > 0) //check for a buffer of 0 size or smaller
                            {
                                byte[] buffer2 = new byte[buffer2lenght];
                                //read the old filedata and copy it to buffer2
                                readStream.Seek(longBytearrayToInterger(afterImpOffset), 0);
                                readStream.Read(buffer2, 0, buffer2.Length);
                                readStream.Flush();
                                readStream.Close();
                                //write old filedata to new vol file
                                writeStream2.Write(buffer2, 0, buffer2.Length);
                                writeStream2.Flush();
                                writeStream2.Close();
                            }
                            else
                            {
                                readStream.Close();
                                writeStream2.Close();
                            }
                        }
                        else //file to import is not the last and not the first file in the vol
                        {
                            //write old volfile first then imported file and old file again
                            //write the newVolheader to the new vol file
                            writeStream2.Write(newVolHeader, 0, newVolHeader.Length);
                            //write old data, copy data to buffer3 first
                            byte[] firstFileoffset = new byte[4];
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, firstFileoffset, 0, 4); //copy the offset file to import (till this offset we have to copy old data)
                            byte[] buffer3 = new byte[longBytearrayToInterger(firstFileoffset)];
                            readStream.Seek(longBytearrayToInterger(MyGlobals.EndOfHeader), 0); //goto end of header
                            //copy old data (before importfile) to buffer3
                            readStream.Read(buffer3, 0, buffer3.Length);
                            //write old data to new vol file
                            writeStream2.Write(buffer3, 0, buffer3.Length);
                            //write importet file to new vol file
                            writeStream2.Write(importbuffer, 0, importbuffer.Length);
                            //write the rest of the old data to the vol file
                            //make a buffer for the old data
                            byte[] ImpFileoffset = new byte[4];
                            byte[] OldimpFilesize = new byte[4];
                            byte[] afterImpOffset = new byte[4];
                            int iafterImpOffset;
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, ImpFileoffset, 0, 4); //get offset of old importfile
                            Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 32, OldimpFilesize, 0, 4); //get size of old importfile
                            iafterImpOffset = longBytearrayToInterger(ImpFileoffset) + longBytearrayToInterger(MyGlobals.EndOfHeader) + longBytearrayToInterger(OldimpFilesize); //calculate offset of the file after the old importfile
                            afterImpOffset = System.BitConverter.GetBytes(iafterImpOffset);
                            Array.Reverse(afterImpOffset);
                            int buffer2lenght = longBytearrayToInterger(MyGlobals.VolFilesize) - longBytearrayToInterger(afterImpOffset);//make buffer the right size
                            if (buffer2lenght > 0) //check for a buffer of 0 size or smaller
                            {
                                byte[] buffer2 = new byte[buffer2lenght];
                                //read the old filedata and copy it to buffer2
                                readStream.Seek(longBytearrayToInterger(afterImpOffset), 0);
                                readStream.Read(buffer2, 0, buffer2.Length);
                                readStream.Flush();
                                readStream.Close();
                                //write old filedata to new vol file
                                writeStream2.Write(buffer2, 0, buffer2.Length);
                                writeStream2.Flush();
                                writeStream2.Close();
                            }
                            else
                            {
                                readStream.Close();
                                writeStream2.Close();
                            }
                        }
                    }
                    //delete the old vol file and rename the new one (delete the .imp)
                    FileInfo oldfile = new FileInfo(@MyGlobals.VolFilepath);
                    oldfile.Delete();
                    FileInfo newfile = new FileInfo(@MyGlobals.VolFilepath + ".imp");
                    newfile.MoveTo(MyGlobals.VolFilepath);
                    MessageBox.Show("File inserted.");
                }
                else
                {
                    //just write the new content to the right offset
                    //MessageBox.Show("file to import has the same size");
                    byte[] impFileoffset = new byte[4];
                    Array.Copy(MyGlobals.VolFileInfos[FileTree.SelectedNode.Index], 36, impFileoffset, 0, 4);
                    //add endofheader to the fileoffset
                    int realoff = longBytearrayToInterger(impFileoffset) + longBytearrayToInterger(MyGlobals.EndOfHeader);
                    impFileoffset = System.BitConverter.GetBytes(realoff);
                    Array.Reverse(impFileoffset);
                    //create a filestream and write importbuffer to the right offset
                    FileStream writeStream = new FileStream(MyGlobals.VolFilepath, FileMode.Open, FileAccess.Write);
                    writeStream.Seek(realoff, 0);
                    writeStream.Write(importbuffer, 0, importbuffer.Length);
                    writeStream.Flush();
                    writeStream.Close();
                    MessageBox.Show("File inserted.");
                }
            }
            
            

        }

        private void ExtractAll_Click(object sender, EventArgs e)
        {
            //make a dialog to choose a folder
            FolderBrowserDialog folderDlg = new FolderBrowserDialog();
            DialogResult result = folderDlg.ShowDialog();
            string extractallFolder = folderDlg.SelectedPath;

            if (result == DialogResult.OK)
            {
                //for every file do...
                for (int exfilecount = 0; exfilecount < longBytearrayToInterger(MyGlobals.NumberOfFiles); exfilecount++)
                {
                    //get filenames
                    byte[] exFilename = new byte[32];
                    Array.Copy(MyGlobals.VolFileInfos[exfilecount], 0, exFilename, 0, 32);
                    string extractallFilenames = System.Text.Encoding.ASCII.GetString(exFilename);
                    extractallFilenames = extractallFilenames.Trim('\0');
                    using (BinaryWriter binWriter = new BinaryWriter(File.Open(extractallFolder + "\\" + extractallFilenames, FileMode.Create)))
                    {
                        //make extra variables to save the filesize and offset of the file to extract
                        byte[] exFilesize = new byte[4];
                        byte[] exFileoffset = new byte[4];
                        Array.Copy(MyGlobals.VolFileInfos[exfilecount], 32, exFilesize, 0, 4);
                        Array.Copy(MyGlobals.VolFileInfos[exfilecount], 36, exFileoffset, 0, 4);
                        //add endofheader to the fileoffset
                        int realoff = longBytearrayToInterger(exFileoffset) + longBytearrayToInterger(MyGlobals.EndOfHeader);
                        exFileoffset = System.BitConverter.GetBytes(realoff);
                        Array.Reverse(exFileoffset); //freaking bitconvert is giving littleendian values back...
                        //make a buffer of the size of the file to extract
                        byte[] exFilebuffer = new byte[longBytearrayToInterger(exFilesize)];
                        BinaryReader ReadBinary = new BinaryReader(File.Open(MyGlobals.VolFilepath, FileMode.Open));
                        ReadBinary.BaseStream.Seek(longBytearrayToInterger(exFileoffset), 0);
                        exFilebuffer = ReadBinary.ReadBytes(longBytearrayToInterger(exFilesize));
                        //XOR every byte of the exFilebuffer with the XORkey
                        for (int i = 0; i < exFilebuffer.Length; i++)
                        {
                            exFilebuffer[i] = (byte)(exFilebuffer[i] ^ MyGlobals.XORkey);
                        }
                        //finaly write the file
                        binWriter.Write(exFilebuffer);

                        binWriter.Close();
                        ReadBinary.Close();

                    }
                }
                MessageBox.Show("Files extracted.");
            }
            

        }
    }
}
