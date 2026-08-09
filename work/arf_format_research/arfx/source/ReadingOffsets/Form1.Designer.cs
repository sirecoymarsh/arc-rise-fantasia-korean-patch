namespace ReadingOffsets
{
    partial class Form1
    {
        /// <summary>
        /// Erforderliche Designervariable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Verwendete Ressourcen bereinigen.
        /// </summary>
        /// <param name="disposing">True, wenn verwaltete Ressourcen gelöscht werden sollen; andernfalls False.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Vom Windows Form-Designer generierter Code

        /// <summary>
        /// Erforderliche Methode für die Designerunterstützung.
        /// Der Inhalt der Methode darf nicht mit dem Code-Editor geändert werden.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.OpenVolFile = new System.Windows.Forms.OpenFileDialog();
            this.OpenVolButton = new System.Windows.Forms.Button();
            this.TextLogBox = new System.Windows.Forms.TextBox();
            this.FileTree = new System.Windows.Forms.TreeView();
            this.ContextMenuTreeView = new System.Windows.Forms.ContextMenuStrip(this.components);
            this.extractFileToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.importFileToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.TextExfileinfoBox = new System.Windows.Forms.TextBox();
            this.ExtractAll = new System.Windows.Forms.Button();
            this.label1 = new System.Windows.Forms.Label();
            this.ContextMenuTreeView.SuspendLayout();
            this.SuspendLayout();
            // 
            // OpenVolFile
            // 
            this.OpenVolFile.FileName = "OpenVolFile";
            // 
            // OpenVolButton
            // 
            this.OpenVolButton.Location = new System.Drawing.Point(425, 295);
            this.OpenVolButton.Name = "OpenVolButton";
            this.OpenVolButton.Size = new System.Drawing.Size(75, 23);
            this.OpenVolButton.TabIndex = 0;
            this.OpenVolButton.Text = "open .vol...";
            this.OpenVolButton.UseVisualStyleBackColor = true;
            this.OpenVolButton.Click += new System.EventHandler(this.OpenVolButton_Click);
            // 
            // TextLogBox
            // 
            this.TextLogBox.Location = new System.Drawing.Point(284, 16);
            this.TextLogBox.Multiline = true;
            this.TextLogBox.Name = "TextLogBox";
            this.TextLogBox.ReadOnly = true;
            this.TextLogBox.Size = new System.Drawing.Size(216, 183);
            this.TextLogBox.TabIndex = 1;
            // 
            // FileTree
            // 
            this.FileTree.ContextMenuStrip = this.ContextMenuTreeView;
            this.FileTree.Location = new System.Drawing.Point(12, 16);
            this.FileTree.Name = "FileTree";
            this.FileTree.Size = new System.Drawing.Size(266, 273);
            this.FileTree.TabIndex = 2;
            this.FileTree.AfterSelect += new System.Windows.Forms.TreeViewEventHandler(this.FileTree_AfterSelect);
            this.FileTree.NodeMouseClick += new System.Windows.Forms.TreeNodeMouseClickEventHandler(this.FileTree_NodeMouseClick);
            // 
            // ContextMenuTreeView
            // 
            this.ContextMenuTreeView.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.extractFileToolStripMenuItem,
            this.importFileToolStripMenuItem});
            this.ContextMenuTreeView.Name = "ContextMenuTreeView";
            this.ContextMenuTreeView.Size = new System.Drawing.Size(127, 48);
            this.ContextMenuTreeView.Opening += new System.ComponentModel.CancelEventHandler(this.ContextMenuTreeView_Opening);
            // 
            // extractFileToolStripMenuItem
            // 
            this.extractFileToolStripMenuItem.Name = "extractFileToolStripMenuItem";
            this.extractFileToolStripMenuItem.Size = new System.Drawing.Size(126, 22);
            this.extractFileToolStripMenuItem.Text = "extract file";
            this.extractFileToolStripMenuItem.Click += new System.EventHandler(this.extractFileToolStripMenuItem_Click);
            // 
            // importFileToolStripMenuItem
            // 
            this.importFileToolStripMenuItem.Name = "importFileToolStripMenuItem";
            this.importFileToolStripMenuItem.Size = new System.Drawing.Size(126, 22);
            this.importFileToolStripMenuItem.Text = "insert file";
            this.importFileToolStripMenuItem.Click += new System.EventHandler(this.importFileToolStripMenuItem_Click);
            // 
            // TextExfileinfoBox
            // 
            this.TextExfileinfoBox.Location = new System.Drawing.Point(284, 205);
            this.TextExfileinfoBox.Multiline = true;
            this.TextExfileinfoBox.Name = "TextExfileinfoBox";
            this.TextExfileinfoBox.ReadOnly = true;
            this.TextExfileinfoBox.Size = new System.Drawing.Size(216, 84);
            this.TextExfileinfoBox.TabIndex = 3;
            // 
            // ExtractAll
            // 
            this.ExtractAll.Enabled = false;
            this.ExtractAll.Location = new System.Drawing.Point(344, 295);
            this.ExtractAll.Name = "ExtractAll";
            this.ExtractAll.Size = new System.Drawing.Size(75, 23);
            this.ExtractAll.TabIndex = 4;
            this.ExtractAll.Text = "extract all...";
            this.ExtractAll.UseVisualStyleBackColor = true;
            this.ExtractAll.Click += new System.EventHandler(this.ExtractAll_Click);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.ForeColor = System.Drawing.SystemColors.InactiveCaption;
            this.label1.Location = new System.Drawing.Point(13, 295);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(30, 13);
            this.label1.TabIndex = 5;
            this.label1.Text = "RHX";
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(512, 330);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.ExtractAll);
            this.Controls.Add(this.TextExfileinfoBox);
            this.Controls.Add(this.FileTree);
            this.Controls.Add(this.TextLogBox);
            this.Controls.Add(this.OpenVolButton);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Name = "Form1";
            this.Text = "ARFX";
            this.Load += new System.EventHandler(this.Form1_Load);
            this.ContextMenuTreeView.ResumeLayout(false);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.OpenFileDialog OpenVolFile;
        private System.Windows.Forms.Button OpenVolButton;
        private System.Windows.Forms.TextBox TextLogBox;
        private System.Windows.Forms.TreeView FileTree;
        private System.Windows.Forms.ContextMenuStrip ContextMenuTreeView;
        private System.Windows.Forms.ToolStripMenuItem extractFileToolStripMenuItem;
        private System.Windows.Forms.TextBox TextExfileinfoBox;
        private System.Windows.Forms.ToolStripMenuItem importFileToolStripMenuItem;
        private System.Windows.Forms.Button ExtractAll;
        private System.Windows.Forms.Label label1;
    }
}

